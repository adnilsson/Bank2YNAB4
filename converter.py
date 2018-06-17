from datetime import datetime
from collections import namedtuple
import locale
import csv
import warnings
from sys import exit

#TODO:
# 1. Make this file also function as a script. 
#   - specify a bank and input path + call bank2ynab
# 1. create a mapping from  companies in the 'trasaction' field to ynab payees
# 2. User dialog window asking what the payee should be when no payee was found, and add to mapping


# ------- On YnabEntry -------
# Categories will only import if the category already exists in your budget 
# file with the exact same name. Otherwise the categories will be ignored 
# when importing the file. Also, make sure that the categories are listed 
# with the master category, followed by a colon, then the sub category.  
# For example: 
# Everyday Expenses: Groceries
# 
# Payee and category are currently always set to emrty string


class Converter:
    def __init__(self, bankHeader, delimiter):
        # Specified by YNAB4
        self.YNABHeader = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']
        self.YnabEntry  = namedtuple('YnabEntry', ' '.join(self.YNABHeader).lower())

        self.BankEntry = namedtuple('BankEntry', ' '.join(bankHeader).lower()) 
        self.csvDelimiter = delimiter

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
            reader = csv.reader(inputFile, delimiter=self.csvDelimiter)
            try:
                for row in reader:
                    if reader.line_num == 1: # Skip first row (header)
                        continue

                    if (row and len(row) != namedtupleLen(self.BankEntry)):
                        msg = f' expected row length {namedtupleLen(self.BankEntry)},' \
                                f' but got {len(row)} ({row})'
                        warnings.warn(badFormatWarn(msg), RuntimeWarning)
                    elif row:
                        bankRow = self.BankEntry._make(row)
                        for i in toIgnore:
                            if i not in bankRow.transaction:
                                self.readRows.append(bankRow)
                            else:
                                self.ignoredRows.append(bankRow)
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

    def parseRows(self, bankRows):
        for row in bankRows:
            try:
                self.parsedRows.append(self.parseRow(row))
            except (ValueError, TypeError) as e:
                msg = f'\n\t{row}\n\tError: {e}'
                warnings.warn(badFormatWarn(msg), RuntimeWarning)

        print(f'{len(self.parsedRows)}/{len(bankRows)} line(s) successfully parsed ')

        return bankRows

    def parseRow(self, bankline):
        if type(bankline) is not self.BankEntry: 
            raise TypeError(f'{bankline} is not a line from the bank\'s csv-file')
        if not bankline.amount: 
            raise ValueError('A transaction must have an amount')
        if not bankline.date: 
            raise ValueError('A transaction must have a date')

        # payee and memo are not a mandatory fields; set only if they exist
        try:
            payee = bankline.payee
        except AttributeError as e:
            payee = ''

        try:
            memo = bankline.memo
        except AttributeError as e:
            memo = ''

        strAmount = bankline.amount.strip()
        amountSign = '-' if strAmount[0] == '-' else '+'
        
        bankInflow  = strAmount if amountSign == '+' else ''
        bankOutflow = strAmount[1::] if amountSign == '-' else ''

        date = datetime.strptime(bankline.date, '%Y-%m-%d') #convert to date
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
    """
    Perform the conversion from a bank csv-file to YNAB's csv format.
    """
    converter = Converter(bank.header, bank.delimiter)

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
