# jinjawalk
A simple utility for rendering Jinja templates using INI file(s).

This utility will render a tree of [Jinja](https://jinja.palletsprojects.com/) templates using key-value pairs from [configparser](https://docs.python.org/3/library/configparser.html) compatible 
`INI`/`conf` files.

## Basic usage examples
Say you have a `conf/ingredients.ini` ini file:
```text
[cake]
sugar = 1kg
flour = 2kg
```

and a collection of templates, `path/to/templates/`, one of which being `recipe.txt`:
```text
mix {{ config['cake']['sugar'] }} sugar and {{ config['cake']['flour'] }} flour
```

then you can render then entire template tree using:
```python
from jinjawalk import JinjaWalk

walker = JinjaWalk()
walker.walk('conf/ingredients.ini', 'path/to/templates/', 'path/to/output')
```

or alternatively, directly from the commandline:
```bash
./jinjawalk.py --conf=conf/ingredients.ini --source=path/to/templates --output=path/to/output
```
