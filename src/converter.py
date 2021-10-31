from datetime import datetime
from pathlib import Path
from typing import NamedTuple, TypeAlias
import csv
import warnings

from .config import BankConfig, TransactionFormat

# TODO:
# * Make accignore a feature of the bank config file
# * Make this file also function as a script.
#   - specify a bank and input path + call bank2ynab
#
# Category is currently rather useless since an exact match between the
# bank satement category and the YNAB4 category is required, which is
# unrealistic.
#
# ------- On YnabEntry -------
# Text below copied from: http://web.archive.org/web/20160405175101/http://classic.youneedabudget.com/support/article/csv-file-importing
#
# Categories will only import if the category already exists in your budget
# file with the exact same name. Otherwise the categories will be ignored
# when importing the file. Also, make sure that the categories are listed
# with the master category, followed by a colon, then the sub category.
# For example:
# Everyday Expenses: Groceries
#
# Any field can be left blank except the date

StrPair: TypeAlias = tuple[str, str]

class YnabHeader(NamedTuple):
    """ Mapping to the column names specified by YNAB4
    """
    date: str = 'Date'
    payee: str = 'Payee'
    category: str = 'Category'
    memo: str = 'Memo'
    outflow: str = 'Outflow'
    inflow: str = 'Inflow'

class Converter:
    def __init__(self, config: BankConfig):
        self.ynab_header = YnabHeader()
        self.config = config
        self.config.normalizer = normalize

        self.ignoredRows   = []
        self.readRows      = []
        self.parsedRows    = []
        self.numEmptyRows  = 0

    def convert(self, statement_csv: Path, toIgnore=None) -> bool:
        toIgnore = [] if toIgnore is None else toIgnore

        # Attempt to parse input file to a YNAB-formatted csv file
        # May raise OSError
        bankData = self.readInput(statement_csv, toIgnore)
        parsed   = self.parseRows(bankData)

        return self.writeOutput(parsed)

    def readInput(self, statement_csv: Path, toIgnore) -> list[dict[str, str]]:
        with statement_csv.open(encoding='utf-8-sig', newline='')  as f:
            restkey='overflow'
            reader = csv.DictReader(
                f,
                delimiter=self.config.csv_delimiter,
                restkey=restkey,
                skipinitialspace=True, # important since qouting won't work if there is leading whitespace
            )
            reader.fieldnames = [self.config.normalizer(name) for name in reader.fieldnames]
            try:
                for raw_row in reader:
                    if (overflowing_columns := raw_row.get(restkey)):
                        msg = f"Exccess columns found: {overflowing_columns=}"
                        warnings.warn(msg, RuntimeWarning)
                        del raw_row[restkey]

                    row = {k: self.config.normalizer(v) for k, v in raw_row.items()}
                    is_empty = all((len(v) == 0 for v in row.values()))
                    if is_empty:
                        warnings.warn(
                            f'\n\tSkipping empty row {reader.line_num}: {row}',
                            RuntimeWarning)
                        self.numEmptyRows += 1
                    else:
                        if (payee := row.get(self.config.payee_column)) and len(toIgnore) > 0:
                            for i in toIgnore:
                                if i not in payee:
                                    self.readRows.append(row)
                                else:
                                    self.ignoredRows.append(row)
                        else:
                                self.readRows.append(row)
            except csv.Error as e:
                raise OSError(f'file {str(statement_csv)}\n line {row}: {e}')
            finally:
                print('{0}/{1} line(s) successfully read '
                      '(ignored {2} blank line(s) and '
                       '{3} transactions found in accignore).'
                      .format(len(self.readRows), reader.line_num-1, self.numEmptyRows, len(self.ignoredRows)))

        return self.readRows

    def parseRows(self, bankRows):
        for row in bankRows:
            try:
                self.parsedRows.append(self.parseRow(row))
            except (ValueError, TypeError) as e:
                msg = f'\n\t{row}\n\tError: {e}'
                warnings.warn(badFormatWarn(msg), RuntimeWarning)

        print(f'{len(self.parsedRows)}/{len(bankRows)} line(s) successfully parsed ')

        return self.parsedRows

    def _parseAmountField(self, bankline) -> StrPair:
        amount = bankline[self.config.amount_column]
        sign = '-' if amount[0] == '-' else '+'

        outflow = amount[1::] if sign == '-' else ''
        inflow  = amount if sign == '+' else ''

        return outflow, inflow

    def _parseInflowOutflowFields(self, bankline) -> StrPair:
        outflow = bankline.get(self.config.outflow_column, '')
        inflow = bankline.get(self.config.inflow_column, '')

        if outflow == inflow == '':
            warnings.warn("Both outflow and inflow are empty", RuntimeWarning)

        return outflow, inflow

    def parseTransactionValue(self, bankline) -> StrPair:
        transactionParser = None
        match self.config.transaction_format:
            case TransactionFormat.AMOUNT:
                transactionParser = self._parseAmountField
            case TransactionFormat.OUT_IN:
                transactionParser = self._parseInflowOutflowFields
            case _:
                raise RuntimeError(f"{self.config.transaction_format=} is not a valid TransactionFormat")

        if transactionParser is None:
            raise RuntimeError(f'expected {TransactionFormat.AMOUNT} or'
                f' {TransactionFormat.OUT_IN} as transaction'
                f' format, got {self.csvTrasactionFormat=}')

        return transactionParser(bankline)

    def parseRow(self, bankline: dict[str, str]):
        # must have outflow/inflow columns in YNAB4
        outflow, inflow = self.parseTransactionValue(bankline)

        bank_date = bankline[self.config.date_column]
        date = datetime.strptime(bank_date, self.config.date_format) # convert to datetime
        date = date.strftime('%Y/%m/%d')  # YNAB4 desired format

        yh = self.ynab_header # rename
        ynab_row = dict().fromkeys(list(self.ynab_header)) # assert same ordering of keys as self.ynab_header
        ynab_row[yh.date] = date
        ynab_row[yh.outflow] = outflow
        ynab_row[yh.inflow] = inflow
        ynab_row[yh.payee] = bankline.get(self.config.payee_column)
        ynab_row[yh.category] = bankline.get(self.config.category_column)
        ynab_row[yh.memo] = bankline.get(self.config.memo_column)

        return ynab_row

    def writeOutput(self, parsedRows) -> bool:
        hasWritten = False

        if parsedRows == None or len(parsedRows) == 0:
            return hasWritten

        with open('ynabImport.csv', 'w', encoding='utf-8', newline='') as outputFile:
            writer = csv.DictWriter(outputFile, list(self.ynab_header))
            try:
                writer.writeheader()
                writer.writerows(parsedRows)
                hasWritten = True
                print('YNAB csv-file successfully written.')
            except csv.Error as e:
                raise OSError(f'File {outputFile}, line {writer.line_num}: {e}')
            finally:
                return hasWritten

def namedtupleLen(tupleArg: NamedTuple) -> int:
    return len(tupleArg._fields)

def readIgnore():
    accounts = []
    try:
        with open('accignore.txt', encoding='utf-8', newline='') as ignored:
            for account in ignored:
                accounts.append(account)
        msg = f'Ignoring transactions from account(s): {accounts}'
    except OSError:
        msg = 'Parsing all transactions...'
    print(msg)
    return accounts


def badFormatWarn(entry):
    return f'\n\tIncorrectly formated row:{entry}\n\t Skipping...'


def normalize(value: str) -> str:
    return value.strip().lower()


def bank2ynab(bank: BankConfig, statement_csv: Path):
    """ Perform the conversion from a bank csv-file to YNAB's csv format
    """
    converter = Converter(config=bank)

    # Check for accignore.txt and obtain a list of ignored accounts.
    try:
        ignoredAccounts = readIgnore()
    except OSError:
        ignoredAccounts = []    # It's okay to not have it.

    # Do the conversion:
    # fetch file, attempt parsing, write output, and return results.
    hasConverted = converter.convert(statement_csv, ignoredAccounts)
    return (hasConverted, converter.numEmptyRows, len(converter.ignoredRows),
            len(converter.readRows), len(converter.parsedRows))
