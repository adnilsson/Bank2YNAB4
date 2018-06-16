from tkinter import Tk, StringVar
from tkinter.ttk import Combobox, Frame, Label, Button
from collections import namedtuple
from ynabCSV import main


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


class Application(Tk):
    """
    Main window that can repace the frame that is shown
    https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
    """
    def __init__(self):
        Tk.__init__(self)
        self._frame = None
        self.switch_frame(BankSelection)

    def switch_frame(self, frame_class, args=None):
        """Destroys current frame and replaces it with a new one."""
        new_frame = frame_class(self, args)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        
        self._frame.grid(padx=12, pady=10)
        self._frame.master.title("Bank2YNAB4")
        self._frame.master.resizable(False, False)


class BankSelection(Frame):
    def __init__(self, master=None, args=None):
        Frame.__init__(self, master)

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
        args = main(banks[toKey(self.bankName.get())], self.master)
        self.master.switch_frame(Report, args)

    def getNames(self, banks):
        names = []
        
        for _, b in banks.items():
            names.append(b.name)
        
        names.sort()
        return tuple(names)


class Report(Frame):
    def __init__(self, master, args):
        Frame.__init__(self, master)
        success, blankRows, ignoredRows, linesRead, rowsParsed= args

        readStats = '{0}/{1} lines read ' \
            '(ignored {0} blank lines and ' \
            '{1} transactions found in accignore).'
        readStats = readStats.format(linesRead, linesRead+blankRows+ignoredRows, blankRows, ignoredRows)

        parsedStats = f'{rowsParsed}/{linesRead} lines parsed '

        if not success:
            self.status = "Conversion failed."
        else:
            self.status = "YNAB csv-file successfully written."
        
        self.statusLabel = Label(self, text=self.status)
        self.statusLabel.grid(column=0, row=0, sticky='W', pady=5)

        self.readStatsLabel  = Label(self, text=readStats)
        self.readStatsLabel.grid(column=0, row=1, sticky='W')

        self.parsedStatsLabel = Label(self, text=parsedStats)
        self.parsedStatsLabel.grid(column=0, row=3, sticky='W')

        self.exitButton = Button(self, text="Exit", command=self.master.destroy)
        self.exitButton.grid(column=0, row=4, sticky='E')


app = Application()
app.mainloop()
