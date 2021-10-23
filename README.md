# Bank2YNAB4
Converts from bank transactions exported as CSV to the format accepted by YNAB4.

## Why YNAB4?

Besides the whole UX aspect, YNAB4 was great for two reasons.
1. One-time cost.
2. Data stored locally, with the option of uploading to Dropbox.

The new, web-based YNAB follows a monthly subscription  model.
Paying $7 to make my monthly budget just does not make sense for me.
Also, I don't want to be forced to store all my bank data on their servers.

## Installation

1. Clone or download the repository
2. Refer to the User Guide

### Requirements

* Python 3.8+

# User guide

Using Bank2YNAB4 is straightforward:
1. Run `bank2ynab.py` to launch the application.
2. Select one of the available banks from the drop-down menu.
3. From the dialog, find and select the CSV file from the bank (a header is assumed to exist in the CSV-file).
4. If conversion succeeded, then the converted CSV file is written to `ynabImport.csv` in the same directory as `bank2ynab.py`.

## List of supported banks

* Nordea [SE]
* ICA Banken [SE]
* Revolut ([SE] tested)

## Adding support for additional banks

Banks are defined using TOML-configuration files found in the [banks](banks/) directory.
These are used to tell Bank2YNAB how to interpret the columns in a CSV statement file.
A [template config](banks/template/template.toml) is provided as a starting point for defining a new bank.
Filling out the template should hopefully be clear from the comments.
Nevertheless, a short description can be helpful:
1. Create a new bank config by copying and renaming the template.
2. Give the bank an appropriate `name` and specify the delimiter and date format used in the bank's CSV statements in the `csv` table.
3. Fill out the `ynab_mapping` table with the corresponding column names from the bank's CSV statement.

Some keys in the template's `ynab_mapping` table are optional, however:
* The `date` key **must** exist in the `ynab_mapping` table.
* Two formats for the transaction amount are supported:
   - A single field, indicated by the `amount` key.
   - Separate fields, indicated by keys `outflow` and `inflow`.

   Besides the `date` key, exactly one of these two formats **must** be specified in the `ynab_mapping` table.

The new bank is automatically included in the drop-down menu of available banks.

## Fixing statements exported from Revolut

Unfortunately, Revolut does not export statements in well-formatted CSV.
A problem is that they use comma both as thousands separator and as the value delimiter.
The way you would solve this is to simply surround numbers in quotation marks, change the delimiter, or change the thousands separator.
Alas, they do not do this, and it has been a known issue since at least [2017](https://community.revolut.com/t/statements-in-excel-csv-format-errors/8655).
You can see an example of how an exported file (from 2021) might look like in `tests/example_csv/revolut_v1.csv`.

This repository provides a script that fixes such ill-formed CSV-files.
The approach is to surround any large number (i.e., greater than 999.99) in the file with quotation marks.
The script is tested and documented, and you should be able to figure out how to use it from the help output:

```bash
python scripts/fix_revolut.py --help
```

You can also try it on the examlpe file:
```bash
python scripts/fix_revolut.py tests/example_csv/revolut_v1.csv --out ./
cat revolut_v1_OUT.csv
```