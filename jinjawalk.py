#!/usr/bin/env python3

import argparse
import configparser
import os
import shutil
from jinja2 import Template
from typing import Callable, Union, List
from functools import reduce


def parse_args():
    """Return parsed args when this file is executed rather than imported."""
    parser = argparse.ArgumentParser(
        description="Render of a folder tree of jinja templates, from an INI file.")

    parser.add_argument("source",
                        type=str,
                        help="path to templates to render")
    parser.add_argument("conf",
                        type=str,
                        nargs='+',
                        help="path(s) to the configuration file(s)")
    parser.add_argument("-o", "--output",
                        dest='destination',
                        type=str,
                        help="path to the configuration file (default: render in-place)")
    parser.add_argument("-e", "--extension",
                        type=str,
                        default='',
                        help="only attempt to render files with this extension (and just copy other files); "
                             "the custom extension will be stripped from the rendered filenames")

    declared_args = parser.parse_args()

    return declared_args


def config_path_to_configparser_instance(item: Union[configparser.ConfigParser, str]) -> configparser.ConfigParser:
    """Convert a path string to fully loaded ConfigParser instances.
    If the provided argument is already a ConfigParser instances, it would be returned intact.
    """
    if type(item) is str:
        config = configparser.ConfigParser()
        config.read(item)
        return config
    return item


def merge_configs(config: Union[configparser.ConfigParser, str, List[Union[configparser.ConfigParser, str]]]) \
        -> configparser.ConfigParser:
    """Take a list of ConfigParser instances and path strings to config files, and merge them all into a single
    ConfigParser instance.
    """
    # Convert to list
    if type(config) in [str, configparser.ConfigParser]:
        config = [config]

    # Load all config files
    config = list(map(config_path_to_configparser_instance, config))

    # Get a unique list of all sections
    sections = reduce(lambda s, x: s.union(x.sections()), config, set())

    # Merge all configs section-by-section
    merged = configparser.ConfigParser()
    for section in sections:
        merged[section] = reduce(lambda d, x: dict(**d, **x[section]) if section in x else d, config, {})

    return merged


class JinjaWalk:
    """JinjaWalk() -> new instance of a template tree walker.
    JinjaWalk(filename_filter, filename_modifier) -> new instance with custom filename modifiers
    """
    def __init__(self,
                 filename_filter: Callable[[str], bool] = lambda s: True,
                 filename_modifier: Callable[[str], str] = lambda s: s) -> None:
        self.filename_filter = filename_filter
        self.filename_modifier = filename_modifier

    def walk(self, config: Union[configparser.ConfigParser, str, List[Union[configparser.ConfigParser, str]]],
             source_dir: str, output_dir: str, namespace: str = 'config'):
        """Render a template tree using key-value pairs from given config file(s)"""
        assert namespace == namespace.strip()
        config = merge_configs(config)

        for root, dirs, files in os.walk(source_dir):
            if output_dir is None:
                # render templates in place
                output_folder = root
            else:
                # render templates in a user-specified destination
                relative_root = root[len(source_dir):]
                output_folder = os.path.join(output_dir, relative_root.strip(os.path.sep))
                os.makedirs(output_folder, exist_ok=True)

            for file in files:
                full_source_file_path = os.path.join(root, file)
                if self.filename_filter(file):
                    with open(full_source_file_path, 'r') as fd:
                        data = fd.read()
                    template = Template(data)
                    rendered_template_base_filename = self.filename_modifier(file)
                    full_destination_file_path = os.path.join(output_folder, rendered_template_base_filename)
                    kwargs = {namespace: config}
                    template.stream(**kwargs).dump(full_destination_file_path)
                else:
                    if output_folder != root:
                        # copy is needed only if this is a not in-place rendering (otherwise shutil.SameFileError)
                        shutil.copy(full_source_file_path, output_folder)


if __name__ == '__main__':
    args = parse_args()

    if args.extension != '':
        walker = JinjaWalk(filename_filter=lambda s: s.endswith(args.extension),
                           filename_modifier=lambda s: s[:-len(args.extension)])
    else:
        walker = JinjaWalk()

    walker.walk(args.conf, args.source, args.destination)
