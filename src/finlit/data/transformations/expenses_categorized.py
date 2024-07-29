"""
Create a DataFrame with all expenses with categories and subcategories.
"""

from datetime import datetime

import duckdb
import pandas as pd
import streamlit as st

from finlit.constants import INITAL_MONTH, INITAL_YEAR, TZ


@st.cache_data
def expenses_categorized(
    all_expenses: pd.DataFrame,  # noqa: ARG001
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

    """
    return duckdb.query(
        """
WITH UniqueCategories AS (
    SELECT DISTINCT CATEGORY
    FROM all_expenses
),
ExpensesForPeriod AS (
    SELECT
        CATEGORY,
        SUM(amount_usd) AS expenses_usd,
        SUM(amount_ars) AS expenses_ars
    FROM all_expenses
    GROUP BY CATEGORY
)
SELECT
    uc.CATEGORY AS category,
    COALESCE(efp.expenses_usd, 0) AS expenses_usd,
    COALESCE(efp.expenses_ars, 0) AS expenses_ars
FROM UniqueCategories uc
LEFT JOIN ExpensesForPeriod efp
    ON uc.CATEGORY = efp.CATEGORY
ORDER BY expenses_usd DESC;
       """
    ).to_df()


@st.cache_data
def expenses_categorized_historic(
    all_expenses: pd.DataFrame,  # noqa: ARG001
    periodo: str,
    only_net_expenses: bool,
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
        periodo (str): The period to filter the expenses.
        only_net_expenses (bool): If True, it will return the net expenses.

    """
    period_date = datetime.strptime(periodo, "%Y-%m-%d").replace(tzinfo=TZ).date()
    initial_date = datetime(INITAL_YEAR, INITAL_MONTH, 1, tzinfo=TZ).date()

    month_diff = (
        (period_date.year - initial_date.year) * 12
        + period_date.month
        - initial_date.month
    )

    return duckdb.query(
        f"""
WITH UniqueCategories AS (
    SELECT DISTINCT CATEGORY
    FROM all_expenses
),
ExpensesForPeriod AS (
    SELECT
        CATEGORY,
        SUM(amount_usd) AS expenses_usd,
        SUM(amount_ars) AS expenses_ars
    FROM all_expenses
    WHERE date < '{periodo}-01'::date
        {"AND NOT array_contains(tags, 'exclude')" if only_net_expenses else ""}
    GROUP BY CATEGORY
)
SELECT
    uc.CATEGORY AS category,
    ROUND(COALESCE(efp.expenses_usd, 0) / {month_diff})  AS expenses_usd,
    ROUND(COALESCE(efp.expenses_ars, 0) / {month_diff}) AS expenses_ars
FROM UniqueCategories uc
LEFT JOIN ExpensesForPeriod efp
    ON uc.CATEGORY = efp.CATEGORY
ORDER BY expenses_usd DESC;
       """  # noqa: S608
    ).to_df()
