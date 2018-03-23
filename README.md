# Bank2YNAB4
Converts from bank transactions exported as CSV to the frormat accepted by YNAB4.

## Why YNAB4?

Besides the whole UX aspect, YNAB4 was great for two reasons.
1. One-time cost. 
2. Data stored locally, with Dropbox option.
The new, web-based YNAB follows a monthly supscription model.
Paying $7 to make my monthly budged just does not make sense to me. 
And I don't want to be forced to store all my bank data in their servers.

## Installation

1. Clone or download the repository
2. Refer to the user Guide

### Requirements

* Python 3.6+
* Windows or Linux (Mac might work as well, I have not tried)

# User guide

You might have to make two changes to `ynabCSV.py` prior to running the script:
1. Make sure the `BankEntry` is set to the entry of your bank, for instance, if you want to read a CSV file from Nordea:
    
    ```python
    BankEntry = NordeaEntry
    ``` 

2. Change the `csvDelimiter` accordingly.
 1. Nordea uses `,`
 2. ICA Banken uses `;`
3. Save changes if any were made.

Then, using the script is straightforward:
1. Run `ynabCSV.py`
2. From the dialog, find and select the CSV file from the bank.
3. The converted CSV file is written to `ynabImport.csv` in the same directoy as `ynabCSV.py`.

## Supported banks

* Nordea [SE]
* ICA Banken [SE]
