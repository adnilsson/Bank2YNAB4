import csv
from decimal import Decimal
from pathlib import Path


def examples_dir():
    return find_dir('example_csv')

def bank_configs_dir():
    return find_dir('banks')

def find_dir(dirname: str) -> Path:
    """ Find the path to a directory
    Recursively (from the current directory) look for the the directory.

    Raises RuntimeError if the directory could not be found.
    """
    dir_path = _find_dir(dirname, Path.cwd())
    if dir_path is None:
        raise RuntimeError(f"no directory named '{dirname}' could be found relative to {Path.cwd()}")

    return dir_path

def _find_dir(dirname: str, dir: Path) -> Path | None:
    dirs = (d for d in dir.iterdir() if d.is_dir())
    for d in dirs:
        if d.name == dirname:
            return d

        recurse = _find_dir(dirname, d) # dfs-style
        if recurse is not None:
            return recurse

    return None

def load_test_example(filename: str) -> Path:
    return _file_in_dir(filename, dir=examples_dir())

def load_bank_config(filename: str) -> Path:
    return _file_in_dir(filename, dir=bank_configs_dir())

def load_template_config():
    return _file_in_dir("template.toml", dir=bank_configs_dir() / "template")

def _file_in_dir(filename: str, dir: Path) -> Path:
    for file in dir.iterdir():
        if file.name == filename:
            return file
    raise FileNotFoundError(f"{filename.name} could be found in {dir}")

def _str_to_decimal(decimal: str ) -> Decimal:
    if decimal == '':
        return Decimal('0')

    return Decimal(decimal)


def net_flow(ynab_csv: Path) -> Decimal:
    net = Decimal('0')
    with ynab_csv.open('r', encoding="utf-8-sig", newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            outflow, inflow = [_str_to_decimal(row[key]) for key in ('Outflow', 'Inflow')]
            net = net + inflow - outflow

    return net