from pathlib import Path
from typing import Optional
import pytest


@pytest.fixture
def examples_dir():
    return find_dir('example_csv')

def find_dir(dirname: str) -> Path:
    """ Find the path to a directory
    Recursively (from the current directory) look for the the directory.

    Raises RuntimeError if the directory could not be found.
    """
    dir_path = _find_dir(dirname, Path.cwd())
    if dir_path is None:
        raise RuntimeError(f"no directory named '{dirname}' could be found relative to {Path.cwd()}")

    return dir_path

def _find_dir(dirname: str, dir: Path) -> Optional[Path]:
    dirs = (d for d in dir.iterdir() if d.is_dir())
    for d in dirs:
        if d.name == dirname:
            return d

        recurse = _find_dir(dirname, d) # dfs-style
        if recurse is not None:
            return recurse

    return None

def load_example(filename: str, dir: Path) -> Path:
    for file in dir.iterdir():
        if file.name == filename:
            return file
