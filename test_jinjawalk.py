from unittest import TestCase
import tempfile
import os
from jinjawalk import JinjaWalk
from typing import Callable, Dict
import shutil


def path_joiner(base: str) -> Callable[[str], str]:
    return lambda s: os.path.join(base, s)


def dump_string(file_path: str, s: str):
    with open(file_path, "w") as of:
        print(s, file=of)


def read_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        content = f.read()
    return content


class TestJinjaWalk(TestCase):

    @staticmethod
    def write_dummy_template(destination: str,
                             conf: Dict[str, str],
                             section_name: str = 'section_name',
                             namespace: str = 'config') -> str:
        s = '\n'.join(["line" + str(i+1) + " with {{ " + namespace + "['" + section_name + "']['" + k + "'] }}"
                       for i, k in enumerate(conf)])
        dump_string(destination, s)

        expected_render = '\n'.join([f"line{i+1} with {conf[k]}" for i, k in enumerate(conf)])
        return expected_render

    @staticmethod
    def write_dummy_conf_file(destination: str, conf: Dict[str, str], section_name='section_name'):
        s = f"[{section_name}]\n" + '\n'.join([f"{k} = {conf[k]}" for k in conf])
        dump_string(destination, s)


class TestMultipleInPlace(TestJinjaWalk):

    def setUp(self) -> None:
        self.work_dir = tempfile.mkdtemp()

        conf1 = {"key1": "value1"}
        conf2 = {"key2": "value2"}
        conf3 = {"key3": "value3"}
        self.conf_file_path1 = path_joiner(self.work_dir)('conf1.ini')
        self.conf_file_path2 = path_joiner(self.work_dir)('conf2.ini')
        self.conf_file_path3 = path_joiner(self.work_dir)('conf3.ini')
        self.write_dummy_conf_file(self.conf_file_path1, conf1)
        self.write_dummy_conf_file(self.conf_file_path2, conf2)
        self.write_dummy_conf_file(self.conf_file_path3, conf3)
        self.expected_render = self.write_dummy_template(path_joiner(self.work_dir)('template.txt'),
                                                         {**conf1, **conf2, **conf3})

    def tearDown(self) -> None:
        shutil.rmtree(self.work_dir)

    def test_multiple_in_place(self):

        walker = JinjaWalk()
        walker.walk([self.conf_file_path1, self.conf_file_path2, self.conf_file_path3], self.work_dir, self.work_dir)

        rendered_template = read_file(path_joiner(self.work_dir)('template.txt'))
        self.assertEqual(self.expected_render, rendered_template.strip('\n'))


class TestDefaults(TestJinjaWalk):
    conf = {"key1": "value1", "key2": "value2"}
    list_of_dummy_subdirs = ['.', 'subdir1', 'subdir2']
    list_of_dummy_templates = ['template1.txt', 'template2.txt']

    def setUp(self) -> None:
        self.source_dir = tempfile.mkdtemp()

        self.conf_file_path = path_joiner(self.source_dir)('conf.ini')
        self.write_dummy_conf_file(self.conf_file_path, self.conf)

        subdirs_to_populate = map(path_joiner(self.source_dir), self.list_of_dummy_subdirs)
        for subdir in subdirs_to_populate:
            os.makedirs(subdir, exist_ok=True)
            templates_to_create = map(path_joiner(subdir), self.list_of_dummy_templates)
            for template_path in templates_to_create:
                self.expected_render = self.write_dummy_template(template_path, self.conf)

        self.output_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.output_dir)

    def test_subdirs(self):

        walker = JinjaWalk()
        walker.walk(self.conf_file_path, self.source_dir, self.output_dir)

        subdirs_to_check = map(path_joiner(self.output_dir), self.list_of_dummy_subdirs)
        for subdir in subdirs_to_check:
            rendered_templates_to_check = map(path_joiner(subdir), self.list_of_dummy_templates)
            for template_path in rendered_templates_to_check:
                with self.subTest(template=template_path):
                    rendered_template = read_file(template_path)
                    self.assertEqual(self.expected_render, rendered_template.strip('\n'))
