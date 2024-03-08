"""
Module that contains the IncomeTable class, which is a subclass of the Table class.
"""
from logging import getLogger

import pandas as pd
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text
from sqlalchemy.types import DATE, DECIMAL, TEXT

from pgloader.ledger import Ledger
from pgloader.tables.base_table import Table

logger = getLogger()


class AllIncomeTable(Table):
    """
    Table object for the income table.
    """

    def __init__(self, ledger: Ledger, engine: Engine, table_name: str) -> None:
        """
        Initialize the table  object for the income table.
        """
        logger.debug("Initializing the AllIncomeTable object.")
        super().__init__(ledger, engine, table_name)

    def drop(self) -> None:
        """
        Drop the table in the database.
        """
        with self.engine.connect() as connection:
            logger.debug("Dropping the table %s.", self.table_name)
            connection.execute(
                text(f"DROP TABLE IF EXISTS {self._schema}.{self.table_name}")
            )

            logger.debug("Commiting the transaction.")
            connection.commit()

    def create(self) -> None:
        """
        Create the table in the database.
        """
        with self.engine.connect() as connection:
            logger.debug("Creating the schema 'fin' if it doesn't exist.")
            connection.execute(
                text(
                    f"""
                    CREATE SCHEMA IF NOT EXISTS {self._schema};
                    """
                )
            )

            logger.debug("Creating the table %s.", self.table_name)
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._schema}.{self.table_name} (
                        date DATE NOT NULL,
                        account TEXT NOT NULL,
                        origin TEXT NOT NULL,
                        payee TEXT,
                        narration TEXT NOT NULL,
                        amount_ars DECIMAL NOT NULL,
                        amount_usd DECIMAL NOT NULL
                    );
                    """
                )
            )

            logger.debug("Commiting the transaction.")
            connection.commit()

    def build(self) -> None:
        """
        Build the table in the database.
        """

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
        _, res = self.ledger.run_query(query)
        logger.debug("Query executed successfully. Creating dataframe.")

        df_build = pd.DataFrame(res)

        self.create()

        logger.debug("Inserting the dataframe into the table.")
        df_build.to_sql(
            self.table_name,
            self.engine,
            schema=self._schema,
            index=False,
            if_exists="append",
            dtype={
                "date": DATE,
                "account": TEXT,
                "origin": TEXT,
                "payee": TEXT,
                "narration": TEXT,
                "amount_ars": DECIMAL,
                "amount_usd": DECIMAL,
            },
        )

    def rebuild(self) -> None:
        """
        Drop the table and create it again.

        It calls the create and build method.
        """
        self.drop()
        self.build()
