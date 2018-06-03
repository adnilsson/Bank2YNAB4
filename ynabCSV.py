from datetime import datetime
from collections import namedtuple
from tkinter.filedialog import askopenfilename
import locale
import csv
import warnings
from sys import exit

#TODO:
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


    def convert(self, inputPath, toIgnore=[]):
        if not inputPath:
            return

        # Attempt to parse input file to a YNAB-formatted csv file
        # May raise OSError 
        bankData = self.readInput(inputPath, toIgnore)
        parsed = self.parseRows(bankData)
        self.writeOutput(parsed)


    def readInput(self, inputPath, toIgnore):
        readRows = []
        #toIgnore = readIgnore()
        emptyRows = 0
        ignoredRows = []
        
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
                                readRows.append(bankRow)
                            else:
                                ignoredRows.append(bankRow)
                    else:
                        warnings.warn(
                            f'\n\tSkipping row {reader.line_num}: {row}', 
                            RuntimeWarning)
                        emptyRows += 1
            except csv.Error as e:
                raise OSError(f'file {inputFile}\n line {row}: {e}')    
            else: 
                print('{0}/{1} line(s) successfully read '
                      '(ignored {2} blank line(s) and '
                       '{3} transactions found in accignore).'
                      .format(len(readRows), reader.line_num-1, emptyRows, len(ignoredRows)))
        
        return readRows


    def parseRows(self, bankRows):
        parsedRows = [] 
        for row in bankRows:
            try:
                parsedRows.append(self.parseRow(row))
            except (ValueError, TypeError) as e:
                msg = f'\n\t{row}\n\tError: {e}'
                warnings.warn(badFormatWarn(msg), RuntimeWarning)

        print(f'{len(parsedRows)}/{len(bankRows)} line(s) successfully parsed ')

        return parsedRows


    def parseRow(self, bankline):
        if type(bankline) is not self.BankEntry: 
            raise TypeError(f'{bankline} is not a line from the bank\'s csv-file')
        if not bankline.amount: 
            raise ValueError('A transaction must have an amount')
        if not bankline.date: 
            raise ValueError('A transaction must have a date')

        strAmount = bankline.amount.strip()
        amountSign = '-' if strAmount[0] == '-' else '+'
        
        bankInflow  = strAmount if amountSign == '+' else ''
        bankOutflow = strAmount[1::] if amountSign == '-' else ''

        date = datetime.strptime(bankline.date, '%Y-%m-%d') #convert to date
        dateStr = date.strftime('%Y/%m/%d')    #get string in the desired format

        # payee is not a mandatory field; set only if it exists
        try:
            payee = bankline.payee
        except Exception as e:
            payee = ''

        return self.YnabEntry(date=dateStr, payee=payee, category='', 
                         memo=bankline.memo, outflow=bankOutflow, 
                         inflow = bankInflow)


    def writeOutput(self, parsedRows):
        with open('ynabImport.csv', 'w', encoding='utf-8', newline='') as outputFile:
            writer = csv.writer(outputFile)
            try:
                writer.writerow(self.YNABHeader)
                writer.writerows(parsedRows)
                print('YNAB csv-file successfully written.')
            except (ValueError, TypeError) as e:
                msg =f'{row}\n\tError: {e}'
                warnings.warn(badFormatWarn(msg), RuntimeWarning)
            except csv.Error as e:
                raise OSError(f'File {outputFile}, line {writer.line_num}: {e}')


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


def getFile():
    inputPath = askopenfilename(
                filetypes=[('CSV files', '*.csv'),
                           ('All files', '*'), # Used for debugging only
                           ],
                initialdir='.')
    if inputPath:
        return inputPath
    else: 
        raise OSError('Invalid file path.')


def badFormatWarn(entry):
    return f'\n\tIncorrectly formated row:{entry}\n\t Skipping...'


def main(bank, root):
    Bank2Ynab = Converter(bank.header, bank.delimiter)

    # Check for accignore.txt and obtain a list ofignored accounts. 
    # It's okay to not have it.
    try:
        ignoredAccounts = readIgnore()
    except OSError:
        ignoredAccounts = []

    try:
        inputPath = getFile()
        Bank2Ynab.convert(inputPath, ignoredAccounts)
        root.destroy()
    except (IOError, NameError, OSError) as e:
        print(f'Error: {e}') 

