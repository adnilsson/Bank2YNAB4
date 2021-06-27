# Bank2YNAB4
Converts from bank transactions exported as CSV to the frormat accepted by YNAB4.

## Why YNAB4?

Besides the whole UX aspect, YNAB4 was great for two reasons.
1. One-time cost.
2. Data stored locally, with the option of uploading to Dropbox.

The new, web-based YNAB follows a monthly supscription model.
Paying $7 to make my monthly budget just does not make sense for me.
Also, I don't want to be forced to store all my bank data in their servers.

## Installation

1. Clone or download the repository
2. Refer to the User Guide

### Requirements

* Python 3.8+
* Windows or Linux (Mac might work as well, I have not tried)

# User guide

Using Bank2YNAB4 is straightforward:
1. Run `bank2ynab.py` to launch the application.
2. Select one of the available banks from the drop-down menu.
3. From the dialog, find and select the CSV file from the bank.
4. If conversion suceeded, then the converted CSV file is written to `ynabImport.csv` in the same directoy as `bank2ynab.py`.

## List of supported banks

* Nordea [SE]
* ICA Banken [SE]

## Adding support for additional banks

The supported banks are defined in `banks.py`.
Each bank is defined by its name, csv-header, and csv-delimiter.
Defining a new bank should be quite clear from the existing entries, nevertheless a short description is in due place:
1. Define the new bank's csv-header as a list.
   * Fields `'Date'`, `Transaction`, and `'Amount'` **must** exist in the header for the script to function.
2. Create a new `Bank` tuple that specifies bank name, csv-header, and csv-delimiter.
3. Add the newly created `Bank` tuple to the dictionary of banks. Keys are genereated by calling `toKey` with the bank name as  argument.

Full example:
```python
NewBankHeader = ['Date', 'Transaction', 'Amount', 'Balance']
NewBank = Bank('NewBank', NewBankHeader, ',') # This bank uses comma as its delimiter
banks[toKey(NewBank.name)] = NewBank
```

You should not need to make any further changes!
The new bank is automatically added to the drop-down menu of available banks.
