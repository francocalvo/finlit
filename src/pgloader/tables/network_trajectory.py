"""
Module that contains the IncomeTable class, which is a subclass of the Table class.
"""

from datetime import date, datetime
from logging import getLogger
from typing import Tuple

import numpy as np
import numpy_financial as npf
import pandas as pd
import pytz
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text
from sqlalchemy.types import DATE, FLOAT

from pgloader.ledger import Ledger
from pgloader.tables.base_table import Table

logger = getLogger()

tz = pytz.timezone("America/Argentina/Cordoba")


class NetworthTrajectory(Table):
    """
    Table object for the income table.
    """

    def __init__(self, ledger: Ledger, engine: Engine, table_name: str) -> None:
        """
        Initialize the table  object for the network trajectories.

        Keywords arguments:
        - ledger: Ledger object
        - engine: Engine object
        - table_name: str

        Important attribues:
        - interval: it's the amount of month prior to the current date that we want
            to consider.
        - interest_rate: the yearly rate of return
        - years: the amount of years we want to consider
        - dream: the amount of money we want to have in the future per month.
            it's converted to a yearly amount and then considered as yearly return.

        """
        logger.debug("Initializing the NetworthTrajectory object.")
        super().__init__(ledger, engine, table_name)

        self._interval: int = 6
        self._interest_rate: float = 0.0528
        self._years: int = 30
        self._dream: float = 5000.0
        # self._dream = self._dream * 12 / 0.035  # 3.5% safe withdrawal rate
        self._dream = self._dream * 12 * 30  # 30 times the monthly amount

        today: date = datetime.now(tz).date()
        self._date_until: date = date(today.year, today.month, 1)
        self._date_from: date = self._date_until - relativedelta(months=+self._interval)

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
            logger.debug("Creating the table %s.", self.table_name)
            connection.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self._schema}.{self.table_name} (
                        date DATE NOT NULL,
                        conservative_value FLOAT NOT NULL,
                        probable_value FLOAT NOT NULL,
                        optimal_value FLOAT NOT NULL
                    )
                    """
                )
            )

            logger.debug("Commiting the transaction.")
            connection.commit()

    def _get_date_array(self) -> list[date]:
        period = rrule.rrule(
            rrule.MONTHLY,
            dtstart=date(self._date_until.year, self._date_until.month, 1),
            bymonthday=1,
            count=self._years * 12,
        )

        return [d.date() for d in period]

    def _run_query(self, query: str) -> float:
        _, res = self.ledger.run_query(query)
        try:
            return float(res[0][0].get_only_position().units.number)  # type: ignore # noqa: PGH003
        except IndexError:
            return 0.0

    def _get_expenses(self) -> float:
        """
        Get the expenses from the ledger.
        """

        query = f"""
        SELECT
            SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
        WHERE account ~ '^Expenses'
            AND DATE < DATE('{self._date_until}')
            AND DATE >= DATE('{self._date_from}')
        """

        logger.debug("Running the query to get the expenses.")
        return self._run_query(query)

    def _get_income(self) -> float:
        """
        Get the income from the ledger.
        """
        query = f"""
        SELECT
            SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
        WHERE account ~ ':Job:'
            AND DATE < DATE('{self._date_until}')
            AND DATE >= DATE('{self._date_from}')
        """

        logger.debug("Running the query to get the income.")
        return self._run_query(query)

    def _get_assets(self) -> float:
        """
        Get the assets from the ledger.
        """
        query = f"""
        SELECT
            SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
        WHERE account ~ '^Assets'
            AND DATE < DATE('{self._date_until}')
        """

        logger.debug("Running the query to get the assets.")
        return self._run_query(query)

    def _get_liabilities(self) -> float:
        """
        Get the assets from the ledger.
        """
        query = f"""
        SELECT
            SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
        WHERE account ~ '^Liabilities'
            AND DATE < DATE('{self._date_until}')
        """

        logger.debug("Running the query to get the liabilities.")
        return self._run_query(query)

    def _networth_series(self) -> pd.DataFrame:
        logger.debug("Creating the networth series.")
        periods = rrule.rrule(
            rrule.MONTHLY,
            dtstart=date(self.first_available_year, self.first_available_month, 1),
            until=self._date_until,
        )

        series: list[Tuple[date, float]] = []

        for period in periods:
            query = f"""
                SELECT SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
                WHERE DATE <= DATE('{period.date()}')
                    AND Account ~ '^Assets|^Liabilities'
                """
            amount = self._run_query(query)
            series.append((period.date(), amount))

        return pd.DataFrame(series, columns=["date", "networth"])[:-1]

    def _get_projection(
        self, initial: float, contrib: float, col_name: str
    ) -> pd.DataFrame:
        periods = self._get_date_array()

        logger.debug("Creating the projection for the %s.", col_name)
        logger.debug(
            "Parameters: interest_rate=%s, initial=%s, contrib=%s",
            self._interest_rate / 12,
            initial,
            contrib,
        )
        fv_monthly_contributions = np.array(
            [
                npf.fv(
                    rate=self._interest_rate / 12, nper=month, pmt=-contrib, pv=-initial
                )
                for month in range(self._years * 12)
            ]
        )

        return pd.DataFrame(
            {
                "date": periods,
                col_name: fv_monthly_contributions,
            }
        )

    def _get_ideal_contrib(self, initial: float) -> float:
        logger.debug("Calculating the ideal contribution.")
        return abs(
            float(
                npf.pmt(
                    rate=self._interest_rate / 12,
                    nper=self._years * 12,
                    pv=initial,
                    fv=-int(self._dream),
                )
            )
        )

    def _get_probable_contrib(self) -> float:
        logger.debug("Calculating the probable contribution.")
        incomes = self._get_income()
        expenses = self._get_expenses()

        return (abs(incomes) - abs(expenses)) / self._interval

    def build(self) -> None:
        """
        Build the table in the database.
        """
        logger.debug("Building the table.")

        # Get the initial assets and the initial variables
        initial_assets = self._get_assets()
        probable_contrib = self._get_probable_contrib()
        conservative_contrib = probable_contrib * 0.75
        ideal_contrib = self._get_ideal_contrib(initial_assets)

        logger.info("Initial assets: %s", initial_assets)
        logger.info("Probable contribution: %s", probable_contrib)
        logger.info("Conservative contribution: %s", conservative_contrib)
        logger.info("Ideal contribution: %s", ideal_contrib)

        networth_series = self._networth_series()

        # Get the projections
        df_projection_conservative = pd.concat(
            [
                self._get_projection(
                    initial_assets, conservative_contrib, "conservative_value"
                ),
                networth_series.rename(columns={"networth": "conservative_value"}),
            ]
        )

        df_projection_probable = pd.concat(
            [
                self._get_projection(
                    initial_assets, probable_contrib, "probable_value"
                ),
                networth_series.rename(columns={"networth": "probable_value"}),
            ]
        )

        df_projection_optimal = pd.concat(
            [
                self._get_projection(initial_assets, ideal_contrib, "optimal_value"),
                networth_series.rename(columns={"networth": "optimal_value"}),
            ]
        )

        # Merge the projections
        df_projection = df_projection_conservative.merge(
            df_projection_probable, on="date", how="inner"
        ).merge(df_projection_optimal, on="date", how="inner")

        logger.debug("Creating the table.")
        self.create()

        logger.debug("Inserting the dataframe into the table.")
        df_projection.to_sql(
            self.table_name,
            self.engine,
            schema=self._schema,
            index=False,
            if_exists="append",
            dtype={
                "date": DATE,
                "conservative_value": FLOAT,
                "probable_value": FLOAT,
                "optimal_value": FLOAT,
            },
        )

    def rebuild(self) -> None:
        """
        Drop the table and create it again.

        It calls the create and build method.
        """
        self.drop()
        self.build()
