from pathlib import Path

from util import examples_dir, load_example
from scripts import fix_revolut
from src.converter import bank2ynab
from src.banks import banks


def test_ica_banken_v1(examples_dir):
    csv_path = load_example('ica_banken_v1.csv', examples_dir)

    expect = (True, 0, 0, 5, 5)
    result = bank2ynab(banks['icabanken'], csv_path)
    assert expect == result

def test_nordea_v2(examples_dir):
    csv_path = load_example('nordea_v2.csv', examples_dir)

    expect = (True, 0, 0, 4, 4)
    result = bank2ynab(banks['nordea'], csv_path)
    assert expect == result

def test_revolut_v1(examples_dir, tmpdir):
    csv_path = load_example('revolut_v1.csv', examples_dir)
    out_dir = Path(tmpdir)
    fixed_file = fix_revolut.quote_numbers(csv_path, out_dir=out_dir)

    expect = (True, 0, 0, 6, 6)
    result = bank2ynab(banks['revolut'], fixed_file)
    assert expect == result
