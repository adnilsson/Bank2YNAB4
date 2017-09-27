from datetime import datetime
from collections import namedtuple
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import locale
import csv
import warnings

# Specified by YNAB4
csvHeader = ['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']

# ------- On YnabEntry -------
# Categories will only import if the category already exists in your budget 
# file with the exact same name. Otherwise the categories will be ignored 
# when importing the file. Also, make sure that the categories are listed 
# with the master category, followed by a colon, then the sub category.  
# For example: 
# Everyday Expenses: Groceries
YnabEntry = namedtuple('YnabEntry', 'date payee category memo outflow inflow')
BankEntry = namedtuple('BankEntry', 'date transaction memo amount balance')

#TODO:
# 2. create a dict mapping common companies in the 'trasaction' field to ynab payees
# 3. User dialog window asking what the payee should be when no payee was found. and add to dict


def namedtupleLen(tupleArg):
    return len(tupleArg._fields)


# arg should be a BankEntry
def parseRow(bankline):
    # For my bank's csv-files I need ',' for decimal separator
    # and '.' for thousand separator
    loc = locale.getlocale()
    locale.setlocale(locale.LC_NUMERIC, 'Italian_Italy.1252') 
    
    if type(bankline) is not BankEntry: 
        raise TypeError('{0} is not a line from the bank\'s csv-file'
                        .format(bankline))
    if not bankline.amount: 
        raise ValueError('A transaction must have an amount')

    amount = locale.atof(bankline.amount)
    if abs(amount) < 0.01: 
        raise ValueError('A transaction must be >= 0.01' 
                         'units in the currency used')
    
    bankInflow  = abs(amount) if amount > 0 else ''
    bankOutflow = abs(amount) if amount < 0 else ''

    date = datetime.strptime(bankline.date, '%Y-%m-%d') #covert to date
    dateStr = date.strftime('%Y/%m/%d')    #get string in the desired format

    # Restore previous locale
    locale.setlocale(locale.LC_ALL, loc) 

    return YnabEntry(date=dateStr, payee= '', category='', 
                     memo=bankline.memo, outflow=bankOutflow, 
                     inflow = bankInflow) 


def readInput(inputPath):
    readRows = []
    toIgnore = readIgnore()
    emptyRows = 0
    ignoredRows = []

    with open(inputPath, encoding='utf-8', newline='')  as inputFile:
        reader = csv.reader(inputFile)
        try:
            for row in reader:
                if reader.line_num == 1: # Skip first row (header)
                    continue

                if (row and len(row) != namedtupleLen(BankEntry)):
                    warnings.warn(badFormatWarn(row), RuntimeWarning)
                elif row:
                    bankRow = BankEntry._make(row)
                    for i in toIgnore:
                        if i not in bankRow.transaction:
                            readRows.append(bankRow)
                        else:
                            ignoredRows.append(bankRow)
                else:
                    warnings.warn(
                        '\n\tSkipping row {0}: {1}'
                        .format(reader.line_num, row), RuntimeWarning)
                    emptyRows += 1
        except csv.Error as e:
            sys.exit('file %s\n line %s: %s' % (inputFile, row, e))    
        else: 
            print('{0}/{1} line(s) successfully read '
                  '(ignored {2} blank line(s) and '
                   '{3} transactions found in accignore).'
                  .format(len(readRows), reader.line_num-1, emptyRows, len(ignoredRows)))
    return readRows


def parseRows(bankRows):
    parsedRows = [] 
    for row in bankRows:
        try:
            parsedRows.append(parseRow(row))
        except (ValueError, TypeError) as e:
            msg ='\n\t{0}\n\tError: {1}'.format(row,e)
            warnings.warn(badFormatWarn(msg), RuntimeWarning)
    print('{0}/{1} line(s) successfully parsed '
          .format(len(parsedRows), len(bankRows)))
    return parsedRows


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
            writer.writerow(csvHeader)
            writer.writerows(parsedRows)
        except (ValueError, TypeError) as e:
            msg ='{0}\n\tError: {1}'.format(row,e)
            warnings.warn(badFormatWarn(msg), RuntimeWarning)
        except csv.Error as e:
            sys.exit('file %s, line %d: %s' % (outputFile, writer.line_num, e)) 


def getFile():
    inputPath = askopenfilename(
                filetypes=[('CSV files', '*.csv'),
                           ('All files', '*'), # Used for debugging only
                           ],
                initialdir='.')
    if inputPath:
        return inputPath
    else: 
        raise OSError('Invalid file path')   


def badFormatWarn(entry):
    return '\n\tIncorrectly formated row:{0}\n\t Skipping...'.format(entry)


Tk().withdraw() # keep the root window from appearing        

# Attempt to parse input file to a YNAB-formatted csv file

try:
    inputPath = getFile()
    bankData = readInput(inputPath)
    parsed = parseRows(bankData)
    writeOutput(parsed)
    input("Press any key to exit...")
except (IOError, NameError, OSError) as e:
    print('Failed to locate input file: {0}'.format(e))  
    sys.exit()  
