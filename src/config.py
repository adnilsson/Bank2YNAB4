import enum
from dataclasses import dataclass
import warnings
import tomli
from pathlib import Path
from typing import Any, Callable


class TransactionFormat(enum.Flag):
    """ CSV files can list transactions in one of these formats.
    AMOUNT: the CSV has a single column for the transaction amount
            (can be positive or negative)
    OUT_IN: the CSV has two columns (OUTFLOW and INFLOW). In any row,
            only one of these columns should have a value. The value of
            that column should be positive.

    OUTFLOW and INFLOW currently only exist as helpers to create OUT_IN.
    """
    AMOUNT = enum.auto()
    OUTFLOW = enum.auto()
    INFLOW = enum.auto()
    OUT_IN = OUTFLOW | INFLOW

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
        currency_format: CurrencyFormat,
        date_column: str,
        outflow_column: (str | None)=None,
        inflow_column: (str | None)=None,
        amount_column: (str | None)=None,
        payee_column: (str | None)=None,
        memo_column: (str | None)=None,
        category_column: (str | None)=None,
        csv_delimiter: (str | None)=None,
        normalizer: (Callable[[str], str] | None)=None,
    ):
        if date_column is None or date_column == '':
            raise ValueError(f"The date column name is empty; {date_column=}")
        self._date_column = date_column

        self.name = name
        self.date_format = date_format
        self.csv_delimiter = ',' if csv_delimiter is None else csv_delimiter
        self.currency_format = currency_format

        self._payee_column = payee_column
        self._memo_column = memo_column
        self._category_column = category_column

        # Validate the config's transaction format.
        if amount_column is not None:
            if outflow_column is not None or inflow_column is not None:
                raise ValueError(
                        f"{amount_column=} cannot be combined with outflow/inflow columns "
                        f"({outflow_column=};{inflow_column=})"
                    )
            self._amount_column = amount_column
            self.transaction_format = TransactionFormat.AMOUNT
        elif outflow_column is not None and inflow_column is not None:
            self._outflow_column = outflow_column
            self._inflow_column = inflow_column
            self.transaction_format = TransactionFormat.OUT_IN
        else:
            raise ValueError(
                "Either amount_column or both outflow_column and inflow_column "
                f"must not be None: {amount_column=};{outflow_column=};{inflow_column=}"
            )

        self.normalizer = lambda x: x
        if normalizer is not None:
            self.normalizer = normalizer

    @property
    def date_column(self):
        if self._date_column is None:
            return None

        return self.normalizer(self._date_column)

    @property
    def outflow_column(self):
        if self._outflow_column is None:
            return None

        return self.normalizer(self._outflow_column)

    @property
    def inflow_column(self):
        if self._inflow_column is None:
            return None

        return self.normalizer(self._inflow_column)

    @property
    def amount_column(self):
        if self._amount_column is None:
            return None

        return self.normalizer(self._amount_column)

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
        currency_format = CurrencyFormat(
            thousands_sep=currency_config['thousands_separator'],
            decimal_point=currency_config['decimal_point'],
        )

        csv_config: dict[str, Any] = toml_config['csv']
        date_format = csv_config['date_format']
        csv_delimiter = csv_config.get('delimiter', ',')
        if len(csv_delimiter) != 1:
            raise ValueError(f"The CSV delimiter must be a single character, not '{csv_delimiter}'")

        if csv_delimiter == currency_format.decimal_point == ',':
            warnings.warn(
                "Both the delimiter and decimal point characters are ',' - make "
                "sure all transaction values are properly quoted", UserWarning)
        elif csv_delimiter == currency_format.thousands_sep == ',':
            warnings.warn(
                "Both the delimiter and thousands separator characters are ',' - make "
                "sure all transaction values are properly quoted", UserWarning)

        ynab_mapping = toml_config['ynab_mapping']
        date_column = ynab_mapping['date']
        outflow_column = ynab_mapping.get('outflow')
        inflow_column = ynab_mapping.get('inflow')
        amount_column = ynab_mapping.get('amount')
        payee_column = ynab_mapping.get('payee')
        memo_column = ynab_mapping.get('memo')
        category_column = ynab_mapping.get('category')

        return cls(
            name=name,
            date_format=date_format,
            csv_delimiter=csv_delimiter,
            currency_format=currency_format,
            date_column=date_column,
            outflow_column=outflow_column,
            inflow_column=inflow_column,
            amount_column=amount_column,
            payee_column=payee_column,
            memo_column=memo_column,
            category_column=category_column,
        )