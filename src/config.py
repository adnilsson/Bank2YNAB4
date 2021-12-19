import enum
from dataclasses import dataclass
import warnings
import tomli
from pathlib import Path
from typing import Any, Callable


def _assert_not_empty(column_name: str) -> str:
    if column_name == '':
        raise ValueError('Empty column name')

    return column_name

class TransactionFormat(enum.Flag):
    """ Format for a CSV transaction column
    The semantics of a transaction column can in different depending
    on wether or not the column is signed (AMOUNT) or unsigned
    (OUTFLOW or INFLOW).
    OUTFLOW: the column describes an unsigned transaction amount
            that represents negative cash flow
    OUTFLOW: the column describes an unsigned transaction amount
            that represents positive cash flow
    AMOUNT: the column describes a signed transaction amount
            (can be positive or negative)
    """
    OUTFLOW = enum.auto()
    INFLOW = enum.auto()
    AMOUNT = OUTFLOW & INFLOW

@dataclass(frozen=True)
class TransactionColumn():
    header_key: str
    transaction_format: TransactionFormat

    @classmethod
    def _outflow_column(cls, header_key: str):
        return cls(header_key=header_key, transaction_format=TransactionFormat.OUTFLOW)

    @classmethod
    def _inflow_column(cls, header_key: str):
        return cls(header_key=header_key, transaction_format=TransactionFormat.INFLOW)

    @classmethod
    def from_config(cls, outflows: str | list[str], inflows: str | list[str]) -> list["TransactionColumn"]:
        def to_list(val: str | list[str]) -> list[str]:
            """ Type check the value
            """
            is_str = lambda v: isinstance(v, str)
            if is_str(val):
                return [_assert_not_empty(val)]

            if not isinstance(val, list):
                raise TypeError(f"Key '{val}' is {type(val)}, not a str or list")
            elif not all((is_str(v) for v in val)):
                not_str = list(filter(lambda v: not is_str(v), val))
                raise TypeError(f"Expected only list of str, but found {not_str} in list")

            return list(map(_assert_not_empty, val))

        outflows_list = to_list(outflows)
        inflows_list = to_list(inflows)

        outflows_tc = {cls._outflow_column(oc) for oc in outflows_list}
        inflows_tc = {cls._inflow_column(ic) for ic in inflows_list}

        # Find AMOUNT columns
        transaction_columns = {tc.header_key: tc for tc in outflows_tc | inflows_tc}
        amount_keys = set(outflows_list) & set(inflows_list)
        for k in amount_keys:
            transaction_columns[k] = cls(header_key=k, transaction_format=TransactionFormat.AMOUNT)

        return list(transaction_columns.values())


@dataclass(frozen=True)
class CurrencyFormat:
    thousands_sep: str
    decimal_point: str

    def __post_init__(self):
        if len(self.thousands_sep) > 1:
            raise ValueError("The thousands separator must be empty or a single character, not '{thousands_sep}'")

        if len(self.decimal_point) != 1:
            raise ValueError("The decimal separator must be a single character, not '{decimal_point}'")

class BankConfig():
    def __init__(
        self,
        name: str,
        date_format: str,
        thousands_separator: str,
        decimal_point: str,
        date_column: str,
        outflow_columns: str | list[str],
        inflow_columns: str | list[str],
        payee_column: (str | None)=None,
        memo_column: (str | None)=None,
        category_column: (str | None)=None,
        csv_delimiter: (str | None)=None,
        normalizer: (Callable[[str], str] | None)=None,
    ):
        if name == '':
            raise ValueError(f"The name column name is empty; {name=}")
        self.name = name

        if date_column == '':
            raise ValueError(f"The date column name is empty; {date_column=}")
        self._date_column = date_column

        if date_format == '':
            raise ValueError(f"The date format string is empty; {date_format=}")
        self.date_format = date_format

        self.csv_delimiter = ',' if csv_delimiter is None else csv_delimiter
        if len(self.csv_delimiter) != 1:
            raise ValueError(f"The CSV delimiter must be a single character, not '{csv_delimiter}'")

        self.currency_format = CurrencyFormat(
            thousands_sep=thousands_separator,
            decimal_point=decimal_point,
        )
        if self.csv_delimiter == self.currency_format.decimal_point == ',':
            warnings.warn(
                "Both the delimiter and decimal point characters are ',' - make "
                "sure all transaction values are properly quoted", UserWarning)
        elif csv_delimiter == self.currency_format.thousands_sep == ',':
            warnings.warn(
                "Both the delimiter and thousands separator characters are ',' - make "
                "sure all transaction values are properly quoted", UserWarning)


        self._payee_column = payee_column
        self._memo_column = memo_column
        self._category_column = category_column

        self._transaction_columns = TransactionColumn.from_config(outflow_columns, inflow_columns)

        self.normalizer = lambda x: x
        if normalizer is not None:
            self.normalizer = normalizer # string pre-processing function

    @property
    def date_column(self):
        return self.normalizer(self._date_column)

    @property
    def transaction_columns(self) -> list[TransactionColumn]:
        normalized=[]
        for tc in self._transaction_columns:
            ntc = TransactionColumn(
                header_key=self.normalizer(tc.header_key),
                transaction_format=tc.transaction_format,
            )
            normalized.append(ntc)
        return normalized

    @property
    def payee_column(self):
        if self._payee_column is None:
            return None

        return self.normalizer(self._payee_column)

    @property
    def memo_column(self):
        if self._memo_column is None:
            return None

        return self.normalizer(self._memo_column)

    @property
    def category_column(self):
        if self._category_column is None:
            return None

        return self.normalizer(self._category_column)

    @classmethod
    def from_file(cls, toml_config: Path):
        with toml_config.open(mode='rb') as f:
            config = tomli.load(f)
        return cls.from_dict(config)

    @classmethod
    def from_dict(cls, toml_config: dict[str, Any]):
        name = toml_config['name']

        currency_config = toml_config['currency_format']
        thousands_separator = currency_config['thousands_separator']
        decimal_point = currency_config['decimal_point']

        csv_config: dict[str, Any] = toml_config['csv']
        date_format = csv_config['date_format']
        csv_delimiter = csv_config.get('delimiter', ',')

        ynab_mapping = toml_config['ynab_mapping']
        date_column = ynab_mapping['date']
        outflow_columns = ynab_mapping['outflow']
        inflow_columns = ynab_mapping['inflow']
        payee_column = ynab_mapping.get('payee')
        memo_column = ynab_mapping.get('memo')
        category_column = ynab_mapping.get('category')

        return cls(
            name=name,
            date_format=date_format,
            csv_delimiter=csv_delimiter,
            thousands_separator=thousands_separator,
            decimal_point=decimal_point,
            date_column=date_column,
            outflow_columns=outflow_columns,
            inflow_columns=inflow_columns,
            payee_column=payee_column,
            memo_column=memo_column,
            category_column=category_column,
        )
