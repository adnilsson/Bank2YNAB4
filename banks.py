""" Banks' header configurations.
Stored in a dictionary where the keys are bank names in lowercase and
only alpha-characters. A bank's header should include "date" and
"amount", otherwise it cannot be parsed since YNAB requires these two
fields.
"""
from collections import namedtuple

Bank = namedtuple('Bank', ['name', 'header', 'delimiter'])
banks = dict()

def toKey(name : str) -> str:
    key = [c for c in name if c.isalpha()]
    key = ''.join(key)
    return key.lower()

NordeaOldHeader = ['Date', 'Transaction', 'Memo', 'Amount', 'Balance']
NordeaOld = Bank('Nordea (gamla)', NordeaOldHeader, delimiter=',')
banks[toKey(NordeaOld.name)] = NordeaOld

# All information regarding the payee is in a different field called "Rubrik"
# while "Betalningsmottagare" (i.e, "payee" in English) is empty.
# This makes no sense, but that's the format they currently use.
NordeaHeader = ['Date', 'Amount', "Sender" ,"TruePayee", "Name", "Payee", "Balance", "Currency"]
Nordea = Bank('Nordea', NordeaHeader, delimiter=';')
banks[toKey(Nordea.name)] = Nordea

IcaHeader = ['Date', 'Payee', 'Transaction', 'Memo', 'Amount', 'Balance']
Ica = Bank('ICA Banken', IcaHeader, delimiter=';')
banks[toKey(Ica.name)] = Ica