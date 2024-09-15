"""
Module with the function expenses_historic_ratios.
"""

import logging
from typing import Tuple

import duckdb
import pandas as pd
import streamlit as st

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@st.cache_data
def expenses_monthly_ratios(
    all_expenses: pd.DataFrame,  # noqa: ARG001
    all_income: pd.DataFrame,  # noqa: ARG001
) -> pd.DataFrame:
    """
    Create a DataFrame with all expenses in a given period.

    The DataFrame should contain the following columns:
        - Date: Date of the expense.
        - Category: Category of the expense.
        - Subcategory: Subcategory of the expense.
        - Narration: Description of the expense.
        - Amount_ars: Amount of the expense in ARS.
        - Amount_usd: Amount of the expense in USD.

    Args:
    ----
        all_expenses (pd.DataFrame): DataFrame with all expenses.
        all_income (pd.DataFrame): DataFrame with all income.

    """

    expenses_historic = duckdb.query(
        """
    WITH IncomeSum AS (
        SELECT
            DATE_PART('YEAR', DATE) AS Y,
            DATE_PART('MONTH', DATE) AS M,
            SUM(Amount_Usd) AS Income
        FROM
            all_income
        GROUP BY
            Y,
            M
    ),
    ExpenseSum AS (
        SELECT
            DATE_PART('YEAR', DATE) AS Y,
            DATE_PART('MONTH', DATE) AS M,
            SUM(Amount_Usd) AS Expenses
        FROM
            all_expenses
        GROUP BY
            Y,
            M
    ),
    NetIncomeSum AS (
        SELECT
            DATE_PART('YEAR', DATE) AS Y,
            DATE_PART('MONTH', DATE) AS M,
            SUM(Amount_Usd) AS Income
        FROM
            all_income
        WHERE
            Origin = 'Job'
        GROUP BY
            Y,
            M
    ),
    NetExpenseSum AS (
        SELECT
            DATE_PART('YEAR', DATE) AS Y,
            DATE_PART('MONTH', DATE) AS M,
            SUM(Amount_Usd) AS Expenses
        FROM
            all_expenses
        WHERE
            NOT array_contains(tags, 'exclude')
        GROUP BY
            Y,
            M
    )
    SELECT
        MAKE_DATE(CAST(E.Y AS int), CAST(E.M AS int), 2) AS x,
        ROUND(E.Expenses / I.Income * 100, 2) AS RatioBruto,
        ROUND(NE.Expenses / NI.Income * 100, 2) AS RatioNeto
    FROM
        IncomeSum AS I
        LEFT JOIN ExpenseSum AS E ON I.Y = E.Y
            AND I.M = E.M
        LEFT JOIN NetIncomeSum AS NI ON I.Y = NI.Y
            AND I.M = NI.M
        LEFT JOIN NetExpenseSum AS NE ON I.Y = NE.Y
            AND I.M = NE.M
    WHERE
        E.Y < DATE_PART('YEAR', CURRENT_DATE)
        OR (E.Y = DATE_PART('YEAR', CURRENT_DATE)
            AND E.M <= DATE_PART('MONTH', CURRENT_DATE))
    ORDER BY
        X ASC
            """
    ).to_df()

    expenses_historic = expenses_historic.set_index("x")
    return expenses_historic.reset_index().melt(
        "x", var_name="category", value_name="y"
    )


@st.cache_data
def expense_historic_ratio(
    all_expenses: pd.DataFrame,  # noqa: ARG001
    all_income: pd.DataFrame,  # noqa: ARG001
) -> Tuple[float, float]:
    """
    Create a DataFrame with all expenses in a given period.

    The DataFrame should contain the following columns:
        - Date: Date of the expense.
        - Category: Category of the expense.
        - Subcategory: Subcategory of the expense.
        - Narration: Description of the expense.
        - Amount_ars: Amount of the expense in ARS.
        - Amount_usd: Amount of the expense in USD.

    Args:
    ----
        all_expenses (pd.DataFrame): DataFrame with all expenses.
        all_income (pd.DataFrame): DataFrame with all income.

    """

    results = duckdb.query(
        """
    WITH IncomeSum AS (
        SELECT
            SUM(Amount_Usd) AS Income
        FROM
            all_income
    ),
    ExpenseSum AS (
        SELECT
            SUM(Amount_Usd) AS Expenses
        FROM
            all_expenses
    ),
    NetIncomeSum AS (
        SELECT
            SUM(Amount_Usd) AS NetIncome
        FROM
            all_income
        WHERE
            Origin = 'Job'
    ),
    NetExpenseSum AS (
        SELECT
            SUM(Amount_Usd) AS NetExpenses
        FROM
            all_expenses
        WHERE
            NOT array_contains(tags, 'exclude')
    ),
    Combined AS (
        SELECT
            (SELECT Income FROM IncomeSum) AS Income,
            (SELECT Expenses FROM ExpenseSum) AS Expenses,
            (SELECT NetIncome FROM NetIncomeSum) AS NetIncome,
            (SELECT NetExpenses FROM NetExpenseSum) AS NetExpenses
    )
    SELECT
        ROUND(Expenses / Income * 100, 2) AS RatioBruto,
        ROUND(NetExpenses / NetIncome * 100, 2) AS RatioNeto
    FROM Combined;
            """
    ).to_df()

    return (
        results.iloc[0]["RatioBruto"],
        results.iloc[0]["RatioNeto"],
    )
