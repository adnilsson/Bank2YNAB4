from decimal import Decimal
from pathlib import Path
import random

from hypothesis.strategies import decimals, data, lists, text, integers
from hypothesis import given, settings
import pytest

from scripts import fix_revolut
from util import examples_dir, load_example

_quoter = fix_revolut.NumberQuoter() # class under test
put_into_quotes = _quoter.quote_str_number

# ----------- Hypothesis strategies -----------

def format_num(num: Decimal) -> str:
    """ Place ',' as  thousands separator and round to two decimals"""
    return f'{num:,}'

def insert_quotes(s: str) -> str:
    return f'"{s}"'

# Generate numbers that corrupt any CSV-format that uses comma separators
large_number = decimals(min_value=1000.00, allow_infinity=False,
    allow_nan=False, places=2).map(format_num)
list_of_large_number = integers(min_value=1, max_value=16).flatmap(
    lambda n: lists(large_number, min_size=n, max_size=n)
)

# Generate an incorrect format (NumberQuoter is by default configured to
# search for exactly two decimal digits).
large_number_too_many_or_few_decimals = integers(min_value=1, max_value=12).filter(lambda n: n != 2).flatmap(
    lambda n: decimals(min_value=1000.00, allow_infinity=False,
        allow_nan=False, places=n).map(format_num)
)

# Generate smaller numbers that don't have to be in quotation marks
small_number = decimals(min_value=0.00, max_value=999.99,
    places=2).map(format_num)

# Generate numbers with ',' as thousands separator and surround them with quotation marks.
# This is the expected format in CSV-files that use comma as the value separator.
large_number_in_quotes = large_number.map(insert_quotes)
list_of_large_number_in_quotes = integers(min_value=0, max_value=16).flatmap(
    lambda n: lists(large_number_in_quotes, min_size=n, max_size=n)
)

# ----------- Hypothesis tests -----------

@settings(max_examples=10**4)
@given(num=large_number)
def test_large_num_in_quotes(num: str):
    print(num)
    assert(put_into_quotes(num) == insert_quotes(num))

@settings(max_examples=10**3)
@given(num=small_number)
def test_small_number_not_in_quotes(num: str):
    assert(put_into_quotes(num) == num)

@settings(max_examples=10**3)
@given(num=large_number_in_quotes)
def test_large_number_in_quotes(num: str):
    assert(put_into_quotes(num) == num)

@settings(max_examples=10**3)
@given(num=large_number_too_many_or_few_decimals)
def test_too_many_or_few_decimals(num):
    test_str = f'{num}, {insert_quotes(num)}'
    result = put_into_quotes(test_str)
    assert result == test_str

@settings(max_examples=10**3)
@given(list_of_large_number, list_of_large_number_in_quotes, data())
def test_inject_into_text(large_nums, large_nums_in_quotes, data):
    """
    Insert random text in between examples of quoted and un-quoted large numbers.
    Assert that we find all un-quoted large numbers.

    This test isn't completely robust since we could theoretically generate e.g. 9,000.01
    in the random text, which would contribute to the final count.
    """
    n_bad_format = len(large_nums)

    all_numbers = large_nums # rename
    all_numbers.extend(large_nums_in_quotes)
    random.shuffle(all_numbers)

    padded_nums = []
    some_text = lambda: data.draw(text(max_size=16))
    for num in all_numbers:
        padded_nums.append(f'{some_text()},{num},{some_text()}')

    test_string = ''.join(padded_nums)
    assert len(_quoter._pattern.findall(test_string)) == n_bad_format

# ----------- PyTest unit tests -----------

def test_example_statement(examples_dir):
    csv_path = load_example('revolut_v1.csv', examples_dir)
    revolut_statement = csv_path.read_text()
    quoted = put_into_quotes(revolut_statement)

    # The example statement has the invalid format for large numbers
    # so put_into_quotes should fix (and hence change) the file.
    assert revolut_statement != quoted
    # There are two incorrectly formatted columns in the example statemet
    assert len(_quoter._pattern.findall(revolut_statement)) == 2

    # Fixing a fixed string shold do nothing.
    assert put_into_quotes(quoted) == quoted


def test_replace(examples_dir, tmpdir):
    """ Verify that the orgignal file was overwritten. """
    csv_path = load_example('revolut_v1.csv', examples_dir)
    revolut_statement = csv_path.read_text()

    # copy to a temporary directory
    tmp_csv_path = Path(tmpdir) / csv_path.name
    tmp_csv_path.write_text(revolut_statement)

    quoted_file = fix_revolut.quote_numbers(tmp_csv_path, replace=True)

    assert tmp_csv_path == quoted_file
    assert revolut_statement != quoted_file.read_text()


def test_out_dir(examples_dir, tmpdir):
    """ Verify that the output is written to the expected directory. """
    csv_path = load_example('revolut_v1.csv', examples_dir)

    out_dirs = [Path(tmpdir), Path.cwd(), Path('./')]
    for out_dir in out_dirs:
        quoted_file = fix_revolut.quote_numbers(csv_path, out_dir=out_dir)
        assert out_dir / quoted_file.name == quoted_file
        quoted_file.unlink()


def test_mutex_arguments(examples_dir):
    """ ``replace`` and ``out_dir`` are mutually exclusive. """
    csv_path = load_example('revolut_v1.csv', examples_dir)
    with pytest.raises(ValueError):
        fix_revolut.quote_numbers(csv_path, replace=True, out_dir=examples_dir)

def test_wrong_thousands_sep():
    test_str = '1 000.00, "1 000.00"'
    result = put_into_quotes(test_str)
    assert result == test_str

def test_space_thousands_sep():
    test_str = '1 000.00, "1 000.00"'
    expect = '"1 000.00", "1 000.00"'
    nq = fix_revolut.NumberQuoter(thousands_sep= ' ')
    result = nq.quote_str_number(test_str)
    assert result == expect

def test_no_thousands_sep():
    test_str = '1000.00, "1000.00"'
    expect = '"1000.00", "1000.00"'
    nq = fix_revolut.NumberQuoter(thousands_sep= '')
    result = nq.quote_str_number(test_str)
    assert result == expect

def test_wrong_decimal_sep():
    test_str = '1000,00, "1000,00"'
    nq = fix_revolut.NumberQuoter(thousands_sep= '')
    result = nq.quote_str_number(test_str)
    assert result == test_str

def test_period_thousands_sep_and_comma_decimal_sep():
    test_str = '1.000,00, "1.000,00"'
    expect = '"1.000,00", "1.000,00"'
    nq = fix_revolut.NumberQuoter(thousands_sep= '.', decimal_sep=',')
    result = nq.quote_str_number(test_str)
    assert result == expect

def test_failed_generated_test_1():
    """ This is an example of intput that we do not handle.
    This input will, however, never be seen in practice because in CSV-files
    values must be separated.

    The example is kept as documentation.
    """
    # Is the first quotation mark a dangling end-quote for the frist number or an
    # opening mark for the second?
    test_str = '1,000.00"1,000.00"'

    # Ideally, we'd be able to infer that the quotes in the test_str belong to the
    # second number and surround the first number in new quotation marks.
    expected = '"1,000.00""1,000.00"'
    with pytest.raises(AssertionError):
        assert put_into_quotes(test_str) == expected
