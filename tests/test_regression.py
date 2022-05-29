from pathlib import Path
from decimal import Decimal

from util import load_test_example, load_bank_config, net_flow
from src.converter import bank2ynab
from src.config import BankConfig


def test_revolut_v2_regression_01():
    """
    I discovered that Revolut in their v2 format are inconsistent
    in the number of decimal digits they include.
    For example, they truncate zeros: "3.4" and not "3.40".
    Moreover, if the amount is even, they do not include decimals
    at all: "1000" and not "1000.00".

    The TransactionValueParser assumed a resulution of hundreds
    with zeros padded, i.e., that there are always exactly two
    decimal digits.

    This lead to an incorrect net flow.
    """
    csv_path = load_test_example("regression/revolut_v2_regression_01.csv")
    toml_path = load_bank_config("revolut_v2.toml")
    revolut_config = BankConfig.from_file(toml_path)

    # Do the conversion and sanity check the results
    expect = (True, 0, 0, 5, 5)
    result = bank2ynab(revolut_config, csv_path)
    assert expect == result

    # Assert that the net flow is what we expect
    expected_net_flow = Decimal("-152.37")
    net_converted = net_flow(Path.cwd() / "ynabImport.csv")
    assert expected_net_flow == net_converted
