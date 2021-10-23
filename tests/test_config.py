from os import name
from pathlib import Path
from typing import List
from src.config import BankConfig

import pytest

@pytest.fixture
def bank_config_files() -> List[Path]:
    config_files = [c for c in Path('banks').iterdir() if c.suffix == '.toml']
    if len(config_files) == 0:
        raise FileNotFoundError("No TOML config files found in the 'banks/' directory")

    return config_files

def test_parse_bank_configs(bank_config_files):
    for config in bank_config_files:
        BankConfig.from_file(config)


# ----------- Test invalid inputs -----------

def test_invalid_config_empty():
    config = {}
    with pytest.raises(ValueError):
        BankConfig(name=None, date_column=None, date_format=None)

def test_invalid_config_empty_from_dict():
    config = {}
    with pytest.raises(KeyError):
        BankConfig.from_dict(config)

def test_invalid_config_missing_date():
    with pytest.raises(ValueError):
        BankConfig(name='N', date_format='DF', date_column=None)

def test_invalid_config_missing_date_from_dict():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {},
    }
    with pytest.raises(KeyError):
        BankConfig.from_dict(config)

def test_invalid_config_empty_date_from_dict():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {'date': ''},
    }
    with pytest.raises(ValueError):
        BankConfig.from_dict(config)

def test_invalid_config_missing_date_format():
    with pytest.raises(ValueError):
        BankConfig(name='N', date_format=None, date_column='Date')

def test_invalid_config_missing_date_format_from_dict():
    config = {
        'name': 'N',
        'csv': {},
        'ynab_mapping': {'date': 'D'},
    }
    with pytest.raises(KeyError):
        BankConfig.from_dict(config)

def test_invalid_config_missing_transaction_format():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {'date': 'D'},
    }
    with pytest.raises(ValueError):
        BankConfig.from_dict(config)

def test_invalid_config_amount_and_outflow_inflow():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {'date': 'D', 'amount': 'A', 'outflow': 'O', 'inflow':'I'},
    }
    with pytest.raises(ValueError):
        BankConfig.from_dict(config)

def test_invalid_config_amount_and_outflow():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {'date': 'D', 'amount': 'A', 'outflow': 'O'},
    }
    with pytest.raises(ValueError):
        BankConfig.from_dict(config)

def test_invalid_config_amount_and_inflow():
    config = {
        'name': 'N',
        'csv': {'date_format': 'DF'},
        'ynab_mapping': {'date': 'D', 'amount': 'A', 'inflow':'I'},
    }
    with pytest.raises(ValueError):
        BankConfig.from_dict(config)