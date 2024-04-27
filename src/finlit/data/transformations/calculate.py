"""
Module that contains various functions to calculate financial metrics.
"""

import duckdb
import pandas as pd


def net_expense_ratio(
    all_expenses: pd.DataFrame,  # noqa: ARG001
    all_income: pd.DataFrame,  # noqa: ARG001
) -> int:
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
    return (
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

    return (
        duckdb.query(
            f"""
    SELECT SUM({field})
    FROM transactions"""  # noqa: S608
        )
        .to_df()
        .to_numpy()[0][0]
    )
