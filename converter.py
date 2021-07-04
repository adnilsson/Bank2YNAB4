from datetime import datetime
from collections import namedtuple
from typing import Iterable, Optional, Tuple
import csv
import functools
import warnings
import enum

#TODO:
# * Replace banks.py with a toml config + reader
# * Assert that headers in __REQUIRED_HEADERS are non-empty
# * Make this file also function as a script.
#   - specify a bank and input path + call bank2ynab

# Category is currently always set to empty string.

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

class TransactionFormat(enum.Flag):
    """ CSV files can list transactions in one of these formats.
    AMOUNT: the CSV has a single column for the transaction amount
            (can be positive or negative)
    IN_OUT: the CSV has two columns (INFLOW and OUTFLOW). In any row,
            only one of these columns should have a value. The value of
            that column should be positive.

    INFLOW and OUTFLOW only exist as helpers to create IN_OUT.
    """
    AMOUNT = enum.auto()
    INFLOW = enum.auto()
    OUTFLOW = enum.auto()
    IN_OUT = INFLOW | OUTFLOW

    @classmethod
    def match_header(cls, header: list) -> Optional["TransactionFormat"]:
        matches = []
        for h in header:
            if (match := cls.__members__.get(h.upper(), None)) is not None:
                matches.append(match)

        flag = functools.reduce(lambda x, y: x | y, matches) # OR-together all matches
        if flag is cls.IN_OUT:
            return cls.IN_OUT
        elif flag is cls.AMOUNT:
            return cls.AMOUNT

        return None

class Converter:
    __REQUIRED_HEADERS=('date',)

    def __init__(self, bank_header, delimiter, date_format):
        lower_header = [bh.lower() for bh in bank_header]
        for required_header in self.__REQUIRED_HEADERS:
            if required_header not in lower_header:
                raise ValueError(f"'{required_header}' is a required column, but"
                     f" it's not in the bank's configuration header:\n {bank_header}")

        csvTrasactionFormat = TransactionFormat.match_header(lower_header)
        if csvTrasactionFormat is None:
            raise ValueError(f"one of {TransactionFormat.AMOUNT} or both"
                f" {[TransactionFormat.INFLOW, TransactionFormat.OUTFLOW]} is"
                f" reqired, but neither could be found in the"
                f" bank's configuration header:\n {bank_header}")
        self.csvTrasactionFormat = csvTrasactionFormat

        # Specified by YNAB4
        self.YNABHeader = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']
        self.YnabEntry  = namedtuple('YnabEntry', ' '.join(self.YNABHeader).lower())

        alpha_only = lambda x: ''.join([char for char in x if char.isalpha()])
        self.BankEntry = namedtuple('BankEntry', ' '.join([alpha_only(h) for h in lower_header]))
        self.csvDelimiter = delimiter
        self.dateFormat = date_format

        self.ignoredRows   = []
        self.readRows      = []
        self.parsedRows    = []
        self.numEmptyRows  = 0

    def convert(self, inputPath, toIgnore=[]):
        if not inputPath:
            return

        # Attempt to parse input file to a YNAB-formatted csv file
        # May raise OSError
        bankData = self.readInput(inputPath, toIgnore)
        parsed   = self.parseRows(bankData)

        return self.writeOutput(parsed)

    def readInput(self, inputPath, toIgnore):
        with open(inputPath, encoding='utf-8', newline='')  as inputFile:
            header = inputFile.readline()  # assume that the first row is a header and consume it
            print(f'CSV header of {inputPath}: {header}')
            reader = csv.reader(inputFile, delimiter=self.csvDelimiter, skipinitialspace=True)
            try:
                for row in reader:
                    if (row and len(row) != namedtupleLen(self.BankEntry)):
                        msg = f' expected row length {namedtupleLen(self.BankEntry)},' \
                                f' but got {len(row)} ({row})'
                        warnings.warn(badFormatWarn(msg), RuntimeWarning)
                    elif row:
                        bankRow = self.BankEntry._make(strip_whitespace(row))
                        if 'payee' in bankRow._fields:
                            for i in toIgnore:
                                if i not in bankRow.payee:
                                    self.readRows.append(bankRow)
                                else:
                                    self.ignoredRows.append(bankRow)
                        else:
                                self.readRows.append(bankRow)
                    else:
                        warnings.warn(
                            f'\n\tSkipping row {reader.line_num}: {row}',
                            RuntimeWarning)
                        self.numEmptyRows += 1
            except csv.Error as e:
                raise OSError(f'file {inputFile}\n line {row}: {e}')
            else:
                print('{0}/{1} line(s) successfully read '
                      '(ignored {2} blank line(s) and '
                       '{3} transactions found in accignore).'
                      .format(len(self.readRows), reader.line_num-1, self.numEmptyRows, len(self.ignoredRows)))

        return self.readRows

    def readOptionalField(self, lambdaFun, alt=''):
        try:
            res = lambdaFun()
        except AttributeError:
            res = alt
        return res

    def parseRows(self, bankRows):
        for row in bankRows:
            try:
                self.parsedRows.append(self.parseRow(row))
            except (ValueError, TypeError) as e:
                msg = f'\n\t{row}\n\tError: {e}'
                warnings.warn(badFormatWarn(msg), RuntimeWarning)

        print(f'{len(self.parsedRows)}/{len(bankRows)} line(s) successfully parsed ')

        return self.parsedRows

    @staticmethod
    def _parseAmountField(bankline) -> Tuple[str, str]:
        amount = bankline.amount
        amountSign = '-' if amount[0] == '-' else '+'

        bankOutflow = amount[1::] if amountSign == '-' else ''
        bankInflow  = amount if amountSign == '+' else ''

        return bankOutflow, bankInflow

    @staticmethod
    def _parseInflowOutflowFields(bankline) -> Tuple[str, str]:
        return bankline.outflow, bankline.inflow

    def parseTransactionValue(self, bankline) -> Tuple[str, str]:
        transactionParser = None
        if self.csvTrasactionFormat is TransactionFormat.AMOUNT:
            transactionParser = self._parseAmountField
        elif self.csvTrasactionFormat is TransactionFormat.IN_OUT:
            transactionParser = self._parseInflowOutflowFields

        if transactionParser is None:
            raise RuntimeError("expected expected AMOUNT or IN_OUT as transaction"
                f' format, got {self.csvTrasactionFormat=}')

        return transactionParser(bankline)

    def parseRow(self, bankline):
        if type(bankline) is not self.BankEntry:
            raise TypeError(f'{bankline} is not a line from the bank\'s csv-file')

        # payee and memo are not mandatory fields; set only if they exist
        payee = self.readOptionalField(lambda: bankline.payee)
        memo  = self.readOptionalField(lambda: bankline.memo)

        bankOutflow, bankInflow = self.parseTransactionValue(bankline)

        date = datetime.strptime(bankline.date, self.dateFormat) #convert to date
        dateStr = date.strftime('%Y/%m/%d')    # desired format

        return self.YnabEntry(date=dateStr, payee=payee, category='',
                         memo=memo, outflow=bankOutflow,
                         inflow = bankInflow)

    def writeOutput(self, parsedRows):
        hasWritten = False

        if(parsedRows == None or len(parsedRows) == 0):
            return hasWritten

        with open('ynabImport.csv', 'w', encoding='utf-8', newline='') as outputFile:
            writer = csv.writer(outputFile)
            try:
                writer.writerow(self.YNABHeader)
                writer.writerows(parsedRows)
                hasWritten = True
                print('YNAB csv-file successfully written.')
            except csv.Error as e:
                raise OSError(f'File {outputFile}, line {writer.line_num}: {e}')
            finally:
                return hasWritten

def strip_whitespace(row: Iterable):
    return [value.strip() for value in row]

def namedtupleLen(tupleArg):
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


def bank2ynab(bank, csvFilePath):
    """ Perform the conversion from a bank csv-file to YNAB's csv format
    """
    converter = Converter(bank.header, bank.delimiter, bank.date_format)

    # Check for accignore.txt and obtain a list ofignored accounts.
    try:
        ignoredAccounts = readIgnore()
    except OSError:
        ignoredAccounts = []    # It's okay to not have it.

    # Do the conversion:
    # fetch file, attempt parsing, write output, and return results.
    hasConverted = converter.convert(csvFilePath, ignoredAccounts)
    return (hasConverted, converter.numEmptyRows, len(converter.ignoredRows),
            len(converter.readRows), len(converter.parsedRows))
