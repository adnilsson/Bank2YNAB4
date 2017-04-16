from datetime import datetime
from collections import namedtuple
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import locale
import csv
import warnings

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

# 5. Let user hardcode transactions that should be ignored.

def namedtupleLen(tupleArg):
    return len(tupleArg._fields)

# For some reason, I can't get locale.atoi to behave, so I use this instead.
def strToInt(floatString):
    return int(locale.atof(floatString))  

# arg should be a BankEntry
def parseRow(bankline):
    # For my bank's csv-files I need ',' for decimal separator
    # and '.' for thousand separator
    loc = locale.getlocale()
    locale.setlocale(locale.LC_NUMERIC, 'Italian_Italy.1252') 
    
    if type(bankline) is (not BankEntry): raise TypeError('the given argument is not a line from the bank\'s csv-file')
    if bankline.amount == False: raise ValueError('A transaction must have an amount')

    amount = locale.atof(bankline.amount)
    if abs(amount) < 0.01: raise ValueError('A transaction must be of more than 0.01 units in the currency used')
    
    bankInflow  = abs(amount) if amount > 0 else ''
    bankOutflow = abs(amount) if amount < 0 else ''

    date = datetime.strptime(bankline.date, '%Y-%m-%d') #covert to date
    dateStr = date.strftime('%Y/%m/%d')    #get string in the desired format

    # Restore previous locale
    locale.setlocale(locale.LC_ALL, loc) 

    return YnabEntry(date=dateStr, payee= '', category='', memo=bankline.memo, outflow=bankOutflow, inflow = bankInflow) 

def getFile():
    inputPath = askopenfilename(
                filetypes=[('CSV files', '*.csv'),
                           ('All files', '*'),
                           ],
                initialdir='.')
    if inputPath:
        file = open(inputPath, encoding='utf-8', newline='')
        return file
    else: raise OSError('Invalid file path')   

def badFormatWarn(entry):
    return 'Incorrectly formated row:\n{0}\n Skipping...'.format(entry)

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing        

# Attempt to parse input file to a YNAB-formatted csv file 
try:
    with getFile() as inputFile:
        with open('ynabImport.csv', "w", encoding='utf-8', newline='') as outputFile:
            reader = csv.reader(inputFile)
            writer = csv.writer(outputFile)
            writer.writerow(csvHeader)

            try:
                for row in reader:
                    if reader.line_num == 1:    # Skip first row
                        continue
                    if (row and len(row) != namedtupleLen(BankEntry)):
                        warnings.warn(badFormatWarn(row), RuntimeWarning) 
                    elif (row):
                        try:
                            parsedRow = parseRow(BankEntry._make(row))
                            print(parsedRow)
                            writer.writerow(parsedRow)
                        except (ValueError, TypeError):
                            warnings.warn(badFormatWarn(row), RuntimeWarning)
            except csv.Error as e:
                sys.exit('file %s, line %d: %s' % (inputFile, reader.line_num, e))
except (IOError, NameError, OSError) as e:
    print('Failed to load input file: {0}'.format(e))
else:
    print("Done")
    
 
