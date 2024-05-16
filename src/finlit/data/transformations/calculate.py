"""
Module that contains various functions to calculate financial metrics.
"""

import logging
from datetime import date, datetime

import duckdb
import numpy_financial as npf
import pandas as pd

from finlit.constants import TZ
from finlit.data.ledger import Ledger

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def net_expense_ratio(
    all_expenses: pd.DataFrame,  # noqa: ARG001
    all_income: pd.DataFrame,  # noqa: ARG001
) -> float:
    """
    Calculate the net expense ratio.

    The net expense ratio is calculated as the ratio between the total expenses.

    The all_expenses DataFrame should contain the following columns:
        - Date: Date of the expense.
        - Subcategory: Subcategory of the expense.
        - Amount_usd: Amount of the expense in USD.

    The all_income DataFrame should contain the following columns:
        - Date: Date of the income.
        - Origin: Origin of the income.
        - Amount_usd: Amount of the income in USD.


    Args:
    ----
        all_expenses (pd.DataFrame): DataFrame with all expenses.
        all_income (pd.DataFrame): DataFrame with all income.

    """
    return float(
        duckdb.query(
            """
    WITH IncomeSum AS (
        SELECT
            EXTRACT(YEAR FROM Date) AS Y,
            EXTRACT(MONTH FROM Date) AS M,
            SUM(Amount_Usd) AS Income
        FROM
            all_income
        WHERE
            Origin = 'Job'
        GROUP BY
            Y,
            M
    ),
    ExpenseSum AS (
        SELECT
            EXTRACT(YEAR FROM Date) AS Y,
            EXTRACT(MONTH FROM Date) AS M,
            SUM(Amount_Usd) AS Expenses
        FROM
            all_expenses
        WHERE
            Subcategory != 'Comisiones'
            AND narration != 'Comprar lavasecarropas Samsung Eco Bubble IA 9.5kg'
        GROUP BY
            Y,
            M
    )
    SELECT
        E.Expenses / I.Income
    FROM
        IncomeSum AS I
        INNER JOIN ExpenseSum AS E ON I.Y = E.Y
            AND I.M = E.M
        """
        )
        .to_df()
        .to_numpy()[0][0]
    )


def sum_field(transactions: pd.DataFrame, field: str) -> float:  # noqa: ARG001
    """
    Calculate the total expenses in a given period.
    """

    return float(
        duckdb.query(
            f"""
    SELECT SUM({field})
    FROM transactions"""  # noqa: S608
        )
        .to_df()
        .to_numpy()[0][0]
    )


def average_income(
    all_income: pd.DataFrame,  # noqa: ARG001
    trailing_months: int,
    *,
    only_type: list[str] | None = None,
) -> float:
    """
    Calculate the average income.
    """
    now = datetime.now(tz=TZ)

    # Last day of last month
    until_date_dt: date = date(now.year, now.month, 1) - pd.DateOffset(days=1)
    until_date: str = until_date_dt.strftime("%Y-%m-%d")

    from_date: str = (until_date_dt - pd.DateOffset(months=trailing_months)).strftime(
        "%Y-%m-%d"
    )

    if only_type is None:
        conditional_query = f"""
            WHERE DATE <= '{until_date}'::DATE
            AND DATE > '{from_date}'::DATE
        """
    else:
        conditions = ", ".join([f"'{net}'" for net in only_type])
        conditional_query = f"""
            WHERE Origin IN ({conditions})
            AND DATE < '{until_date}'::DATE
            AND DATE >= '{from_date}'::DATE
        """

    return (
        float(
            duckdb.query(
                f"""
            SELECT SUM(Amount_Usd)
            FROM all_income
            {conditional_query}
        """  # noqa: S608
            )
            .to_df()
            .to_numpy()[0][0]
        )
        / trailing_months
    )


def average_expenses(
    all_expenses: pd.DataFrame,
    trailing_months: int,
    *,
    net_type: list[str] | None = None,
) -> float:
    """
    Calculate the average expenses.
    """
    until_date: str = datetime.now(tz=TZ).strftime("%Y-%m-%d")
    from_date: str = (
        datetime.now(tz=TZ) - pd.DateOffset(months=trailing_months)
    ).strftime("%Y-%m-%d")

    if net_type is None:
        conditional_query = f"""
            WHERE DATE < '{until_date}'::DATE
            AND DATE >= '{from_date}'::DATE
        """
    else:
        conditions = ", ".join([f"'{net}'" for net in net_type])
        conditional_query = f"""
            WHERE Subcategory NOT IN ({conditions})
            AND DATE < '{until_date}'::DATE
            AND DATE >= '{from_date}'::DATE
        """

    return float(
        duckdb.query(
            f"""
            SELECT SUM(Amount_Usd)
            FROM all_expenses
            {conditional_query}
        """  # noqa: S608
        )
        .to_df()
        .to_numpy()[0][0]
        / trailing_months
    )


def assets(ledger: Ledger, date_until: datetime | None) -> float:
    """
    Get the assets from the ledger.

    Args:
    ----
        ledger (Ledger): Ledger object.
        date_until (datetime): Date until which to calculate the net worth.

    """
    query = f"""
        SELECT
            SUM(convert(Position, 'USD', Date)) as amount_usd
        WHERE Account ~ '^Assets'
            {"and Date < '{self._date_until}'::DATE)" if date_until else ""}
        """

    _, res = ledger.run_query(query)
    try:
        return float(res[0][0].get_only_position().units.number)  # type: ignore # noqa: PGH003
    except IndexError:
        return 0.0


def liabilities(ledger: Ledger, date_until: datetime | None) -> float:
    """
    Get the assets from the ledger.

    Args:
    ----
        ledger (Ledger): Ledger object.
        date_until (datetime): Date until which to calculate the net worth.

    """
    query = f"""
        SELECT
            SUM(convert(Position, 'USD', Date)) as amount_usd
        WHERE Account ~ '^Liabilities'
            {"and Date < '{self._date_until}'::DATE)" if date_until else ""}
        """

    _, res = ledger.run_query(query)
    try:
        return float(res[0][0].get_only_position().units.number)  # type: ignore # noqa: PGH003
    except IndexError:
        return 0.0


def net_worth(ledger: Ledger, date_until: datetime | None = None) -> float:
    """
    Get the net worth from the ledger.

    Args:
    ----
        ledger (Ledger): Ledger object.
        date_until (datetime): Date until which to calculate the net worth.

    """
    return assets(ledger, date_until) - liabilities(ledger, date_until)


def optimal_contribution(
    initial: float, return_rate: float, years: float, dream_total: float
) -> float:
    """
    Get the optimal contribution for the networth trajectory.

    The optimal contribution is the amount of money that the user should
    contribute to their net worth to reach their FIRE goal.

    Args:
    ----
        initial (float): The initial net worth.
        return_rate (float): The yearly return rate.
        years (float): The amount of years to reach the goal.
        dream_total (float): The total amount of money to reach the goal.

    """
    logger.debug("Calculating the optimal contribution.")
    logger.debug("Params: %s", (initial, return_rate, years, dream_total))
    return abs(
        float(
            npf.pmt(
                rate=return_rate / 12,
                nper=years * 12,
                pv=initial,
                fv=-int(dream_total),
            )
        )
    )


def coast_fire(dream: float, rate_of_return: float, years_to_retire: float) -> float:
    """
    Calculate the Coast FIRE number.

    The Coast FIRE number is the amount of money that the user needs to have
    in their net worth to reach their FIRE goal without contributing more
    money to their net worth.

    Args:
    ----
        dream (float): The total amount of money to reach the goal.
        rate_of_return (float): The yearly return rate.
        years_to_retire (float): The amount of years to reach the goal.

    """

    return abs(
        float(
            npf.pv(
                rate=rate_of_return / 12,
                nper=years_to_retire * 12,
                pmt=0,
                fv=-int(dream),
            )
        )
    )
