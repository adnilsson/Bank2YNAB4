import util
import pytest

from converter import bank2ynab
from banks import banks

@pytest.fixture
def examples_dir():
    return util.find_dir('example_csv')

def test_ica_banken(examples_dir):
    csv_path = util.load_example('ica_banken_v1.csv', examples_dir)

    expect = (True, 0, 0, 5, 5)
    result = bank2ynab(banks['icabanken'], csv_path)
    assert expect == result

def test_nordea_v2(examples_dir):
    csv_path = util.load_example('nordea_v2.csv', examples_dir)

    expect = (True, 0, 0, 4, 4)
    result = bank2ynab(banks['nordea'], csv_path)
    assert expect == result
