"""
Module that contains the ExpensesTable class, which is a subclass of the Table class.
"""

from logging import getLogger
from typing import Any

import pandas as pd

from finlit.data.datasets.dataset import Dataset
from finlit.data.ledger import Ledger

logger = getLogger()


class AllExpensesDataset(Dataset):
    """
    Table object for the expenses table.
    """

    def __init__(self, ledger: Ledger, table_name: str) -> None:
        """
        Initialize the table  object for the expenses table.
        """
        super().__init__(ledger, table_name)

    def _unpack_frozenset(self, x: frozenset) -> list[str]:
        """
        Unpack the frozenset.
        """
        if not x:
            return [""]
        # (a,) = x
        # return a
        return list(x)

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
            NUMBER(CONVERT(POSITION, 'USD', DATE)) AS amount_usd,
            FIRST(tags) AS tags
        WHERE account ~ '^Expenses'
        ORDER BY date DESC
        """

        _types, res = self.ledger.run_query(query)

        all_expenses = pd.DataFrame(res)
        all_expenses["tags"] = all_expenses["tags"].apply(self._unpack_frozenset)

        # logger.info(all_expenses["tag"].unique())

        return all_expenses
