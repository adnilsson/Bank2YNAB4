from pathlib import Path

from tests.util import load_test_example, load_bank_config, load_template_config, net_flow
from bank2ynab.converter import convert
from bank2ynab.config import BankConfig


def test_ica_banken_v1():
    csv_path = load_test_example("ica_banken_v1.csv")
    toml_path = load_bank_config("ica_banken_v1.toml")
    ica_config = BankConfig.from_file(toml_path)

    expect = (True, 0, 0, 5, 5)
    result = convert(ica_config, csv_path)
    assert expect == result


def test_nordea_v2():
    csv_path = load_test_example("nordea_v2.csv")
    toml_path = load_bank_config("nordea_v2.toml")
    nordea_config = BankConfig.from_file(toml_path)

    expect = (True, 0, 0, 4, 4)
    result = convert(nordea_config, csv_path)
    assert expect == result


def test_revolut_v2():
    csv_path = load_test_example("revolut_v2.csv")
    toml_path = load_bank_config("revolut_v2.toml")
    revolut_config = BankConfig.from_file(toml_path)

    expect = (True, 0, 0, 5, 5)
    result = convert(revolut_config, csv_path)
    assert expect == result


def test_identity():
    csv_path = load_test_example("example_ynab.csv")
    toml_path = load_template_config()
    template_config = BankConfig.from_file(toml_path)

    expect = (True, 0, 0, 2, 2)
    result = convert(template_config, csv_path)
    assert expect == result

    net_bank = net_flow(csv_path)
    net_converted = net_flow(Path.cwd() / "ynabImport.csv")
    assert net_bank == net_converted
    print(f"{net_converted=}")
