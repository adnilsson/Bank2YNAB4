from datetime import datetime
from collections import namedtuple
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import locale
import csv
import warnings

#TODO:
# 1. create a mapping from  companies in the 'trasaction' field to ynab payees
# 2. User dialog window asking what the payee should be when no payee was found, and add to mapping
# 3. Dynamically change banks (config file or dialog)


# Specified by YNAB4
YNABHeader = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']

# Bank Header. 
NordeaHeader = ['Date', 'Transaction', 'Memo', 'Amount', 'Balance']
IcaHeader = ['Date', 'Payee', 'Transaction', 'Memo', 'Amount', 'Balance']

# ------- On YnabEntry -------
# Categories will only import if the category already exists in your budget 
# file with the exact same name. Otherwise the categories will be ignored 
# when importing the file. Also, make sure that the categories are listed 
# with the master category, followed by a colon, then the sub category.  
# For example: 
# Everyday Expenses: Groceries
# 
# Payee and category are currently always set to emrty string
YnabEntry   = namedtuple('YnabEntry', ' '.join(YNABHeader).lower())

NordeaEntry = namedtuple('NordeaEntry', ' '.join(NordeaHeader).lower()) 
IcaEntry    = namedtuple('IcaEntry', ' '.join(IcaHeader).lower())

BankEntry = NordeaEntry    # Change to the namedtuple that represents your bank's csv header
csvDelimiter = ','      # set the delimiter used when parsing the csv file


def namedtupleLen(tupleArg):
    return len(tupleArg._fields)

def parseRow(bankline: BankEntry) -> YnabEntry:

    if type(bankline) is not BankEntry: 
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

    return YnabEntry(date=dateStr, payee=payee, category='', 
                     memo=bankline.memo, outflow=bankOutflow, 
                     inflow = bankInflow)


def parseRows(bankRows: [BankEntry]) -> [YnabEntry]:
    parsedRows = [] 
    for row in bankRows:
        try:
            parsedRows.append(parseRow(row))
        except (ValueError, TypeError) as e:
            msg = f'\n\t{row}\n\tError: {e}'
            warnings.warn(badFormatWarn(msg), RuntimeWarning)

    print(f'{len(parsedRows)}/{len(bankRows)} line(s) successfully parsed ')

    return parsedRows


def readInput(inputPath):
    readRows = []
    toIgnore = readIgnore()
    emptyRows = 0
    ignoredRows = []

    with open(inputPath, encoding='utf-8', newline='')  as inputFile:
        reader = csv.reader(inputFile, delimiter=csvDelimiter)
        try:
            for row in reader:
                if reader.line_num == 1: # Skip first row (header)
                    continue

                if (row and len(row) != namedtupleLen(BankEntry)):
                    msg = f' expected row length {namedtupleLen(BankEntry)},' \
                            f' but got {row}'
                    warnings.warn(badFormatWarn(msg), RuntimeWarning)
                elif row:
                    bankRow = BankEntry._make(row)
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
            sys.exit(f'file {inputFile}\n line {row}: {e}')    
        else: 
            print('{0}/{1} line(s) successfully read '
                  '(ignored {2} blank line(s) and '
                   '{3} transactions found in accignore).'
                  .format(len(readRows), reader.line_num-1, emptyRows, len(ignoredRows)))
    return readRows


def readIgnore():
    accounts = []
    with open('accignore.txt', encoding='utf-8', newline='') as ignored:
        for account in ignored:
            accounts.append(account)
    return accounts


def writeOutput(parsedRows):
    with open('ynabImport.csv', 'w', encoding='utf-8', newline='') as outputFile:
        writer = csv.writer(outputFile)
        try:
            writer.writerow(YNABHeader)
            writer.writerows(parsedRows)
        except (ValueError, TypeError) as e:
            msg =f'{row}\n\tError: {e}'
            warnings.warn(badFormatWarn(msg), RuntimeWarning)
        except csv.Error as e:
            sys.exit(f'File {outputFile}, line {writer.line_num}: {e}')


def getFile():
    inputPath = askopenfilename(
                filetypes=[('CSV files', '*.csv'),
                           ('All files', '*'), # Used for debugging only
                           ],
                initialdir='.')
    if inputPath:
        return inputPath
    else: 
        raise OSError('Invalid file path: {inputPath}\n')   


def badFormatWarn(entry):
    return f'\n\tIncorrectly formated row:{entry}\n\t Skipping...'


if __name__ == "__main__":

    Tk().withdraw() # keep the root window from appearing        

    # Attempt to parse input file to a YNAB-formatted csv file
    try:
        inputPath = getFile()
        bankData = readInput(inputPath)
        parsed = parseRows(bankData)
        writeOutput(parsed)
        input("Press Return to exit...")
    except (IOError, NameError, OSError) as e:
        print(f'Failed to locate input file: {e}')  
        sys.exit()  