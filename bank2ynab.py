from tkinter import Tk, StringVar
from tkinter.ttk import Combobox, Frame, Label, Button
from collections import namedtuple
from ynabCSV import main


#BANKNAMES = ('Nordea', 'ICA')
Bank = namedtuple('Bank', ['name', 'header', 'delimiter'])
banks = dict()

def toKey(name : str) -> str:
    key = [c for c in name if c.isalpha()]
    key = ''.join(key)
    return key.lower()


NordeaHeader = ['Date', 'Transaction', 'Memo', 'Amount', 'Balance']
Nordea = Bank('Nordea', NordeaHeader, delimiter=',')
banks[toKey(Nordea.name)] = Nordea

IcaHeader = ['Date', 'Payee', 'Transaction', 'Memo', 'Amount', 'Balance']
Ica = Bank('ICA Banken', IcaHeader, delimiter=';')
banks[toKey(Ica.name)] = Ica


class Application(Frame):
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(padx=12, pady=10)
        self.createWidgets()


    def createWidgets(self):
        self.label = Label(self, text="Choose Your Bank:")
        self.label.grid(column=0, row=0, sticky='W', ipadx=2)

        banknames = self.getNames(banks)
        self.bankName = StringVar()
        self.bankName.set(banknames[0])

        self.bankChosen = Combobox(self, width=12, textvariable=self.bankName)
        self.bankChosen['values'] = banknames
        self.bankChosen.grid(column=1, row=0)

        self.confirm = Button(self, text="Ok", command=self.convert)
        self.confirm.grid(column=0, row=1, columnspan=2, sticky='E', pady=5)

    def convert(self):
        empry, ignored, read = main(banks[toKey(self.bankName.get())], self.master)

        self.master.destroy()

    def getNames(self, banks):
        names = []
        
        for _, b in banks.items():
            names.append(b.name)
        
        names.sort()
        return tuple(names)


app = Application()
app.master.title("Bank2YNAB")
app.mainloop()
