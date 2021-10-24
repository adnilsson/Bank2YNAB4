from pathlib import Path
from src.config import BankConfig
from util import load_template_config

import pytest


@pytest.fixture
def bank_config_files() -> list[Path]:
    config_files = [c for c in Path("banks").iterdir() if c.suffix == ".toml"]
    if len(config_files) == 0:
        raise FileNotFoundError("No TOML config files found in the 'banks/' directory")

    return config_files


@pytest.fixture
def valid_config_dict() -> dict[str, str | list[str]]:
    return {
        "name": "test-config",
        "csv": {
            "date_format": "this format is not validated in the config",
        },
        "currency_format": {
            "thousands_separator": "",
            "decimal_point": ".",
        },
        "ynab_mapping": {
            "date": "Date",
            "outflow": "Outflow",
            "inflow": "Inflow",
        },
    }


def test_valid_config_dict(valid_config_dict):
    BankConfig.from_dict(valid_config_dict)


def test_parse_bank_configs(bank_config_files):
    for config in bank_config_files:
        BankConfig.from_file(config)


def test_load_template_config():
    config = load_template_config()
    BankConfig.from_file(config)


# ----------- Test invalid inputs -----------


def test_invalid_args():
    with pytest.raises((ValueError, TypeError)):
        BankConfig(
            name=None,
            date_column=None,
            date_format=None,
            thousands_separator=None,
            decimal_point=None,
            outflow_columns=[],
            inflow_columns=[],
        )


def test_invalid_config_empty():
    config = {}
    with pytest.raises(KeyError):
        BankConfig.from_dict(config)


def test_invalid_config_missing_date_from_dict(valid_config_dict):
    del valid_config_dict["ynab_mapping"]["date"]
    with pytest.raises(KeyError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_empty_date_from_dict(valid_config_dict):
    valid_config_dict["ynab_mapping"]["date"] = ""
    with pytest.raises(ValueError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_missing_date_format_from_dict(valid_config_dict):
    del valid_config_dict["csv"]["date_format"]
    with pytest.raises(KeyError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_missing_inflow(valid_config_dict):
    del valid_config_dict["ynab_mapping"]["inflow"]
    with pytest.raises(KeyError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_missing_outflow(valid_config_dict):
    del valid_config_dict["ynab_mapping"]["outflow"]
    with pytest.raises(KeyError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_missing_currency_format(valid_config_dict):
    del valid_config_dict["currency_format"]
    with pytest.raises(KeyError):
        BankConfig.from_dict(valid_config_dict)


def test_invalid_config_invalid_currency_format_thousands(valid_config_dict):
    fmts = [
        {"thousands_separator": ",,", "decimal_point": "."},
        {"thousands_separator": "", "decimal_point": ".."},
    ]
    for fmt in fmts:
        valid_config_dict["currency_format"] = fmt
        with pytest.raises(ValueError):
            BankConfig.from_dict(valid_config_dict)
