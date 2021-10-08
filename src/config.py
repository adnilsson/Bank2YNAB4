from typing import Any, Dict, Optional
import tomli
from pathlib import Path

from .converter import TransactionFormat


class BankConfig():
    def __init__(
        self,
        name: str,
        date_format: str,
        date_column: str,
        outflow_column: Optional[str]=None,
        inflow_column: Optional[str]=None,
        amount_column: Optional[str]=None,
        payee_column: Optional[str]=None,
        memo_column: Optional[str]=None,
        category_column: Optional[str]=None,
        csv_delimiter: Optional[str]=None,
    ):
        if date_column is None or date_column == '':
            raise ValueError(f"The date column name is empty; {date_column=}")
        self.date_column = date_column

        self.name = name
        self.date_format = date_format
        self.csv_delimiter = ',' if csv_delimiter is None else csv_delimiter

        self.payee_column = payee_column
        self.memo_column = memo_column
        self.category_column = category_column

        # Validate the transaction format. This can either be (1) an amount
        # or (2) an outflow and an inflow.
        if amount_column is not None:
            if outflow_column is not None or inflow_column is not None:
                raise ValueError(
                        f"{amount_column=} cannot be combined with outflow/inflow columns "
                        f"({outflow_column=};{inflow_column=})"
                    )
            self.amount_column = amount_column
            self.transaction_format = TransactionFormat.AMOUNT
        elif outflow_column is not None and inflow_column is not None:
            self.outflow_column = outflow_column
            self.inflow_column = inflow_column
            self.transaction_format = TransactionFormat.IN_OUT
        else:
            raise ValueError(
                "Either amount_column or both outflow_column and inflow_column "
                f"must not be None: {amount_column=};{outflow_column=};{inflow_column=}"
            )

    @classmethod
    def from_file(cls, toml_config: Path):
        with toml_config.open(mode='rb') as f:
            config = tomli.load(f)
        return cls.from_dict(config)

    @classmethod
    def from_dict(cls, toml_config: Dict[str, Any]):
        name = toml_config['name']

        csv_config: Dict[str, Any] = toml_config['csv']
        date_format = csv_config['date_format']
        csv_delimiter = csv_config.get('delimiter')

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
            date_column=date_column,
            outflow_column=outflow_column,
            inflow_column=inflow_column,
            amount_column=amount_column,
            payee_column=payee_column,
            memo_column=memo_column,
            category_column=category_column,
        )