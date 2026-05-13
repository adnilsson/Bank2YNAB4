from pathlib import Path
from tkinter import Tk, StringVar, Toplevel, Message
from tkinter.ttk import Combobox, Frame, Button, Label
from tkinter.filedialog import askopenfilename
from src.converter import bank2ynab
from src.config import BankConfig

PADX = 12
PADY = 10

BANK_DIR = Path("./banks")

###################################
#           GUI-code
###################################


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

        self._frame.grid(padx=PADX, pady=PADY)
        self._frame.master.title("Bank2YNAB4")
        self._frame.master.resizable(False, False)


class BankSelection(Frame):
    def __init__(self, master=None, args=None):
        Frame.__init__(self, master)
        banks = [BankConfig.from_file(b) for b in BANK_DIR.iterdir() if b.suffix == '.toml']
        banks.sort(key=lambda b: b.name)
        self.banks = banks
        self.createWidgets()

    def createWidgets(self):
        self.label = Label(self, text="Choose Your Bank:")
        self.label.grid(column=0, row=0, sticky="W", ipadx=2)

        banknames = [b.name for b in self.banks]
        self.bankName = StringVar()
        self.bankName.set(banknames[0])

        self.bankChosen = Combobox(self, width=12, textvariable=self.bankName)
        self.bankChosen["values"] = banknames
        self.bankChosen.grid(column=1, row=0)

        self.confirm = Button(self, text="Ok", command=self.convert)
        self.confirm.grid(column=0, row=1, columnspan=2, sticky="E", pady=5)

    def convert(self):
        try:
            inputPath = self.getFile()
            bank = self.banks[self.bankChosen.current()]
        except ValueError as e:
            pass  # No file selected
        else:
            try:
                result = bank2ynab(bank, inputPath)
                self.master.switch_frame(Report, result)
            except (NameError, OSError, ValueError, TypeError) as e:
                Error(self, e)

    def getFile(self) -> Path:
        inputPath = askopenfilename(filetypes=[("CSV files", "*.csv")], initialdir=".")
        if inputPath:
            return Path(inputPath)
        else:
            raise ValueError("No file selected")


class Report(Frame):
    def __init__(self, master, args):
        Frame.__init__(self, master)

        self.createLabels(args)

        self.exitButton = Button(self, text="Exit", command=self.master.destroy)
        self.exitButton.grid(column=0, row=4, sticky="E")

    def createLabels(self, args):
        success, blankRows, ignoredRows, linesRead, rowsParsed = args

        readStats = f"{linesRead}/{linesRead+blankRows+ignoredRows} rows read"
        if blankRows + ignoredRows != 0:
            ignoreStats = (
                f" (ignored {blankRows} blank rows and "
                f"{ignoredRows} transactions found in accignore)."
            )
            readStats = readStats + ignoreStats

        parsedStats = f"{rowsParsed}/{linesRead} rows parsed "

        if not success:
            self.status = "Conversion failed."
        else:
            self.status = "YNAB csv-file successfully written."

        self.statusLabel = Label(self, text=self.status)
        self.statusLabel.grid(column=0, row=0, sticky="W", pady=5)

        self.readStatsLabel = Label(self, text=readStats)
        self.readStatsLabel.grid(column=0, row=1, sticky="W")

        self.parsedStatsLabel = Label(self, text=parsedStats)
        self.parsedStatsLabel.grid(column=0, row=3, sticky="W")


class Error(Toplevel):
    """Pop-up for displaying an error message"""

    def __init__(self, master, arg):
        Toplevel.__init__(self, master, padx=PADX, pady=PADY)
        self.title("Error")

        self.msg = Message(self, text=arg, aspect=380)
        self.msg.grid(column=0, row=0, pady=5)
        self.columnconfigure(0, minsize=180)

        button = Button(self, text="Dismiss", command=self.destroy)
        button.grid(column=0, row=1)


if __name__ == "__main__":
    app = Application()
    app.mainloop()
