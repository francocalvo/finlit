"""
Module that contains the ExpensesTable class, which is a subclass of the Table class.
"""

from logging import getLogger
from typing import Any

import pandas as pd
from finlit.data.datasets.dataset import Dataset
from finlit.data.ledger import Ledger
from sqlalchemy.engine import Engine

logger = getLogger()


class AllExpensesDataset(Dataset):
    """
    Table object for the expenses table.
    """

    def __init__(self, ledger: Ledger, engine: Engine, table_name: str) -> None:
        """
        Initialize the table  object for the expenses table.
        """
        super().__init__(ledger, engine, table_name)

    def build(self, **_: dict[str, Any]) -> pd.DataFrame:
        """
        Build the table in the database.
        """
        query = """
        SELECT
            date AS date,
            account AS account,
            LEAF(ROOT(account, 2)) as category,
            LEAF(ROOT(account, 3)) as subcategory,
            payee AS payee,
            narration AS narration,
            NUMBER(CONVERT(POSITION, 'ARS', DATE)) AS amount_ars,
            NUMBER(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
        WHERE account ~ '^Expenses'
        ORDER BY date DESC
        """

        _types, res = self.ledger.run_query(query)

        return pd.DataFrame(res)
