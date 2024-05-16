"""
Module that contains the IncomeTable class, which is a subclass of the Table class.
"""

from dataclasses import dataclass
from datetime import date, datetime
from logging import getLogger
from typing import Tuple

import numpy as np
import numpy_financial as npf
import pandas as pd
import streamlit as st
from dateutil import rrule
from dateutil.relativedelta import relativedelta

from finlit.constants import INITAL_MONTH, INITAL_YEAR, TZ
from finlit.data.ledger import Ledger
from finlit.data.transformations import calculate

logger = getLogger()


@dataclass
class TrajectoryParams:
    """
    Dataclass for the parameters of the trajectory.
    """

    trailing_months: int = 6
    return_rate: float = 0.0528
    years: int = 30
    swr: float = 3.5
    dream: float = 5000.0
    save_rate: float = 75
    first_year: int = INITAL_YEAR
    first_month: int = INITAL_MONTH
    income: float = 0.0
    expenses: float = 0.0
    net_worth: float = 0.0

    @property
    def dream_total(self) -> float:
        """
        Return the total amount of money we want to have in the future.
        """
        return self.dream * 12 / (self.swr / 100)

    def __hash__(self) -> int:
        """
        Return the hash of the object.
        """
        return hash(
            (
                self.trailing_months,
                self.return_rate,
                self.years,
                self.swr,
                self.dream,
                self.save_rate,
                self.first_year,
                self.first_month,
                self.income,
                self.expenses,
                self.net_worth,
            )
        )


class NetworthTrajectory:
    """
    Table object for the income table.
    """

    def __init__(
        self,
        ledger: Ledger,
        trajectory_params: TrajectoryParams,
    ) -> None:
        """
        Initialize the table  object for the network trajectories.

        Keywords arguments:
        - ledger: Ledger object
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

        self.ledger: Ledger = ledger
        self.params = trajectory_params

        today: date = datetime.now(TZ).date()
        self._date_until: date = date(today.year, today.month, 1)
        self._date_from: date = self._date_until - relativedelta(
            months=+self.params.trailing_months
        )

    def _get_date_array(self, *, add_offset: bool = False) -> list[date]:
        initial_date = datetime(
            year=INITAL_YEAR, month=INITAL_MONTH, day=1, tzinfo=TZ
        ).date()

        offset = (
            (
                (self._date_until.year - initial_date.year) * 12
                + self._date_until.month
                - initial_date.month
            )
            if add_offset
            else 0
        )

        return list(
            rrule.rrule(
                rrule.MONTHLY,
                dtstart=self._date_until if not add_offset else initial_date,
                bymonthday=1,
                count=self.params.years * 12 + offset,
            )
        )

    def _run_query(self, query: str) -> float:
        _, res = self.ledger.run_query(query)
        try:
            return float(res[0][0].get_only_position().units.number)  # type: ignore # noqa: PGH003
        except IndexError:
            return 0.0

    def networth_series(self) -> pd.DataFrame:
        """
        Return the networth series.

        The networth series is the series of the networth for each month.
        It counts from the initial date until the current date.
        """
        periods = rrule.rrule(
            rrule.MONTHLY,
            dtstart=date(self.params.first_year, self.params.first_month, 1),
            until=self._date_until,
        )

        logger.debug(
            "Networth series. Periods start: %s. End: %s", periods[0], periods[-1]
        )

        series: list[Tuple[date, float]] = []

        for period in periods:
            query = f"""
                SELECT SUM(CONVERT(POSITION, 'USD', DATE)) AS amount_usd
                WHERE DATE <= DATE('{period.date()}')
                    AND Account ~ '^Assets|^Liabilities'
                """
            amount = self._run_query(query)
            series.append((period, amount))

        return pd.DataFrame(series, columns=["date", "networth"])

    @st.cache_data
    def _get_projection(
        _self,  # noqa: N805
        initial: float,
        contrib: float,
        col_name: str,
    ) -> pd.DataFrame:
        periods = _self._get_date_array()  # noqa: SLF001

        fv_monthly_contributions = np.array(
            [
                npf.fv(
                    rate=_self.params.return_rate / 12,
                    nper=month,
                    pmt=-contrib,
                    pv=-initial,
                )
                for month in range(_self.params.years * 12)
            ]
        )

        return pd.DataFrame(
            {
                "date": periods,
                col_name: fv_monthly_contributions,
            }
        )

    @st.cache_data(
        hash_funcs={
            "finlit.data.transformations.networth_projections.NetworthTrajectory": lambda x: (  # noqa: E501
                networth_hash(x.ledger, x.params)
            ),
        },
    )
    def build(self) -> pd.DataFrame:
        """
        Build the dataframe for the network trajectories.
        """

        income = self.params.income
        expenses = self.params.expenses
        net_worth = self.params.net_worth

        # Get the initial assets and the initial variables
        probable_contrib = income - expenses
        possible_contrib = income * self.params.save_rate / 100
        conservative_contrib = probable_contrib * 0.75
        optimal_contrib = calculate.optimal_contribution(
            net_worth,
            self.params.return_rate,
            self.params.years,
            self.params.dream_total,
        )

        logger.debug("Building the networth trajectory.")
        logger.debug("Income: %s. Type: %s", income, type(income))
        logger.debug("Expenses: %s. Type: %s", expenses, type(expenses))
        logger.debug("Net worth: %s", net_worth)
        logger.debug("Possible contribution: %s", possible_contrib)
        logger.debug("Probable contribution: %s", probable_contrib)
        logger.debug("Conservative contribution: %s", conservative_contrib)
        logger.debug("Ideal contribution: %s", optimal_contrib)

        networth_series = self.networth_series()
        # Get the projections
        df_projection_conservative = pd.concat(
            [
                self._get_projection(
                    net_worth, conservative_contrib, "conservative_value"
                ),
                networth_series.rename(columns={"networth": "conservative_value"}),
            ]
        )

        df_projection_probable = pd.concat(
            [
                self._get_projection(net_worth, probable_contrib, "probable_value"),
                networth_series.rename(columns={"networth": "probable_value"}),
            ]
        )

        df_projection_optimal = pd.concat(
            [
                self._get_projection(net_worth, optimal_contrib, "optimal_value"),
                networth_series.rename(columns={"networth": "optimal_value"}),
            ]
        )

        df_possible = pd.concat(
            [
                self._get_projection(net_worth, possible_contrib, "possible_value"),
                networth_series.rename(columns={"networth": "possible_value"}),
            ]
        )

        # Remove repeated dates
        df_possible = df_possible.drop_duplicates(subset=["date"])
        df_projection_conservative = df_projection_conservative.drop_duplicates(
            subset=["date"]
        )
        df_projection_probable = df_projection_probable.drop_duplicates(subset=["date"])
        df_projection_optimal = df_projection_optimal.drop_duplicates(subset=["date"])

        # df_possible.set_index("date", inplace=True)
        # df_projection_conservative.set_index("date", inplace=True)
        # df_projection_probable.set_index("date", inplace=True)
        # df_projection_optimal.set_index("date", inplace=True)

        # Merge the projections
        return (
            df_projection_conservative.merge(
                df_projection_probable, on="date", how="inner"
            )
            .merge(df_projection_optimal, on="date", how="inner")
            .merge(df_possible, on="date", how="inner")
        )

    # @st.cache_data(
    #     hash_funcs={
    #         "finlit.data.transformations.networth_projections.NetworthTrajectory": lambda x: ( # noqa: E501
    #             hash(x.params)
    #         ),
    #     },
    # )
    def build_coast_fire(self) -> pd.DataFrame:
        """
        Build the dataframe for the coast fire.
        """

        coast_number = calculate.coast_fire(
            self.params.dream_total, self.params.return_rate, self.params.years
        )

        # Calculate the monthly rate of return
        monthly_rate = self.params.return_rate / 12

        # Generate a date range from today monthly until the retirement
        startdate_dt = datetime(
            year=INITAL_YEAR, month=INITAL_MONTH, day=1, tzinfo=TZ
        ).date()

        months_from_start_date = (
            datetime.now(TZ).date().month
            - startdate_dt.month
            + (datetime.now(TZ).date().year - startdate_dt.year) * 12
        )
        logger.debug("Months from start date: %s", months_from_start_date)

        date_range = self._get_date_array(add_offset=True)

        logger.debug("Date range start: %s. End: %s", date_range[0], date_range[-1])

        # Initialize the DataFrame
        df_coast = pd.DataFrame(columns=["date", "age", "coast_value"])

        # Fill the date column
        # My birthday is on 1998/12/29
        born = datetime(1998, 12, 29, tzinfo=TZ)
        df_coast["date"] = date_range
        df_coast["age"] = [
            float(
                today.year
                - born.year
                - ((today.month, today.day) < (born.month, born.day))
            )
            for today in df_coast["date"]
        ]

        current_date = pd.Timestamp.today().normalize()
        months_difference = [
            (today - current_date).days / 30.44 for today in df_coast["date"]
        ]

        # Calculate future value for each month
        df_coast["coast_value"] = [
            coast_number * (1 + monthly_rate) ** month_diff
            for month_diff in months_difference
        ]

        return df_coast


def networth_hash(ledger: Ledger, params: TrajectoryParams) -> int:
    """
    Return the hash of the ledger file.
    """
    return hash(frozenset([hash(ledger), hash(params)]))
