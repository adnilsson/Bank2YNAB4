from datetime import datetime
from collections import namedtuple
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from locale import *
import csv



#csvRows = [['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow']]
YnabEntry = namedtuple('YnabEntry', 'date payee category memo outflow inflow')
BankEntry = namedtuple('BankEntry', 'date transaction memo amount balance')

#TODO:
# 2. create a dict mapping common companies in the 'trasaction' field to ynab payees
# 3. User dialog window asking what the payee should be when no payee was found. and add to dict
# 4. another dict for payees to categories?? (test how well ynab handles empty category-fields first)
# 5. Let user hardcode transactions thah should be ignored.

def strToInt(floatString):
    return int(atof(floatString))

# arg should be a BankEntry
def parseRow(bankline):
    # For my bank's csv-files I need ',' for decimal separator
    # and '.' for thousand separator
    setlocale(LC_NUMERIC, 'Italian_Italy.1252')

    assert type(bankline) is BankEntry, 'the given argument is not a line from the bank\'s csv-file'
    assert strToInt(bankline.amount) != 0, 'A transaction must be of more than 1 unit in the currency used'
    
    bankInflow  = abs(atof(bankline.amount)) if strToInt(bankline.amount) > 0 else ''
    bankOutflow = abs(atof(bankline.amount)) if strToInt(bankline.amount) < 0 else ''

    #entry_date = datetime.strptime('2016-10-26', '%Y-%m-%d') #covert to date
    date = datetime.strptime(bankline.date, '%Y-%m-%d') #covert to date
    dateStr = date.strftime('%Y/%m/%d')    #get string in the desired format

    #TODO: Reset locale
    
    return YnabEntry(date=dateStr, payee= '', category='', memo=bankline.memo, outflow=bankOutflow, inflow = bankInflow) 

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
inputPath = askopenfilename()

try:
    inputFile = open(inputPath, encoding='utf-8', newline='')
except IOError:
    print('Cannot open ', inputPath)
else:
    pass

outputFile = open('ynabImport.csv', "w", encoding='utf-8', newline='')

reader = csv.reader(inputFile)
writer = csv.writer(outputFile)
writer.writerow(['Date', 'Payee', 'Category', 'Memo', 'Outflow', 'Inflow'])

for row in reader:
    if reader.line_num == 1:    # Skip first row
        continue
    if (row and len(row) == 5):
        print(parseRow(BankEntry._make(row)))
        writer.writerow(parseRow(BankEntry._make(row)))
    #csvRows.append(parseRow(row))

### Will crash on empty row (i.e. the last row)
#for entry in map(BankEntry._make, reader):
#    print(entry)
#    if reader.line_num == 1:    # Skip first row
#        continue
#    #writer.writerow(parseRow(entry))
#    #print(parseRow(entry))

inputFile.close()
outputFile.close()

print("Done")
