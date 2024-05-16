"""
Module that contains the AssetDataset class, which is a subclass of the Dataset class.
"""

from logging import getLogger

import duckdb
import pandas as pd
from sqlalchemy.engine import Engine

from finlit.data.datasets.dataset import Dataset
from finlit.data.ledger import Ledger

logger = getLogger()


class BalanceDataset(Dataset):
    """
    Dataset class for the balance sheet table.
    """

    def __init__(self, ledger: Ledger, engine: Engine, table_name: str) -> None:
        """
        Initialize the table  object for the income table.
        """
        logger.debug("Initializing the BalanceDataset object.")
        super().__init__(ledger, engine, table_name)
        self.engine = engine
        self.table_name = table_name
        self.ledger = ledger

    # @st.cache_data(
    #     hash_funcs={
    #         "finlit.data.datasets.all_income.AllIncomeDataset": lambda x: (
    #             ledger_hash(x.ledger)
    #         )
    #     }
    # )
    def _base_data(self, balance_type: str) -> pd.DataFrame:
        """
        Build the table in the database.
        """

        query = f"""
        SELECT 
            YEAR AS Year,
            MONTH AS Month,
            NUMBER(ONLY('USD', SUM(CONVERT(POSITION, 'USD', DATE)))) AS AMOUNT
        WHERE Account ~ '^{balance_type}'
        GROUP BY 1,2
        """

        logger.debug("Running the query to build the table.")
        _, res = self.ledger.run_query(query)  # type: ignore[] WHAT?
        logger.debug("Query executed successfully. Creating dataframe.")

        return pd.DataFrame(res)

    def build(self, **_: dict[str, str]) -> pd.DataFrame:
        """
        Build the table in the database.
        """
        logger.debug("Getting the data for the balance sheet.")
        assets_df = self._base_data("Assets")
        liabilities_df = self._base_data("Liabilities")

        # logger.debug(assets_df.head())
        # logger.debug(liabilities_df.head())

        logger.debug("Merging the dataframes.")
        balance_df: pd.DataFrame = duckdb.query(
            """
            SELECT
                MAKE_DATE(A.YEAR, A.MONTH, 1) AS date,
                SUM(A.AMOUNT) OVER (ORDER BY A.YEAR, A.MONTH) AS assets,
                SUM(B.AMOUNT) OVER (ORDER BY A.YEAR, A.MONTH) AS liabilities,
                SUM(A.AMOUNT) OVER (ORDER BY A.YEAR, A.MONTH) + SUM(B.AMOUNT) OVER (ORDER BY A.YEAR, A.MONTH) AS net_worth
            FROM assets_df A
            INNER JOIN liabilities_df B
            ON A.YEAR = B.YEAR AND A.MONTH = B.MONTH
            WHERE A.YEAR < EXTRACT(YEAR FROM CURRENT_DATE)
            OR (
                A.YEAR = EXTRACT(YEAR FROM CURRENT_DATE)
                AND A.MONTH <= EXTRACT(MONTH FROM CURRENT_DATE)
                )
            """
        ).to_df()

        logger.info("Balance sheet data loaded successfully.")
        logger.info(balance_df.head())
        return balance_df
