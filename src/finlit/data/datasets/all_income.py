"""
Module that contains the IncomeTable class, which is a subclass of the Table class.
"""

from logging import getLogger
from typing import Any

import pandas as pd
import streamlit as st
from finlit.data.datasets.dataset import Dataset
from finlit.data.ledger import Ledger, ledger_hash
from sqlalchemy.engine import Engine

logger = getLogger()


class AllIncomeDataset(Dataset):
    """
    Dataset class for the income table.
    """

    def __init__(self, ledger: Ledger, engine: Engine, table_name: str) -> None:
        """
        Initialize the table  object for the income table.
        """
        logger.debug("Initializing the AllIncomeTable object.")
        super().__init__(ledger, engine, table_name)
        self.engine = engine
        self.table_name = table_name
        self.ledger = ledger

    @st.cache_data(
        hash_funcs={
            "finlit.data.datasets.all_income.AllIncomeDataset": lambda x: (
                ledger_hash(x.ledger)
            )
        }
    )
    def build(self, **_: dict[str, Any]) -> pd.DataFrame:
        """
        Build the table in the database.
        """

        st.session_state["cache_updated"] = True
        logger.debug(ledger_hash(self.ledger))

        query = """
        SELECT
            date AS date,
            account AS account,
            LEAF(ROOT(account, 3)) AS origin,
            payee AS payee,
            narration AS narration,
            NUMBER(CONVERT(ABS(POSITION), 'ARS', DATE)) AS amount_ars,
            NUMBER(CONVERT(ABS(POSITION), 'USD', DATE)) AS amount_usd
        WHERE account ~ '^Income'
        ORDER BY date DESC
        """

        logger.debug("Running the query to build the table.")
        _, res = self.ledger.run_query(query)  # type: ignore[] WHAT?
        logger.debug("Query executed successfully. Creating dataframe.")

        return pd.DataFrame(res)
