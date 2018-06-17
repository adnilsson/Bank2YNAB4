from collections import namedtuple

Bank = namedtuple('Bank', ['name', 'header', 'delimiter'])
banks = dict()

def toKey(name : str) -> str:
    key = [c for c in name if c.isalpha()]
    key = ''.join(key)
    return key.lower()

"""
Banks' header configurations.
Stored in a dictionary where the keys are bank names 
in lowercase and only alpha-characters.
"""
NordeaHeader = ['Date', 'Transaction', 'Memo', 'Amount', 'Balance']
Nordea = Bank('Nordea', NordeaHeader, delimiter=',')
banks[toKey(Nordea.name)] = Nordea

IcaHeader = ['Date', 'Payee', 'Transaction', 'Memo', 'Amount', 'Balance']
Ica = Bank('ICA Banken', IcaHeader, delimiter=';')
banks[toKey(Ica.name)] = Ica