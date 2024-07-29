"""
Create a DataFrame with all expenses in a given period.
"""

import duckdb
import pandas as pd
import streamlit as st


@st.cache_data
def all_expenses_period(
    all_expenses_complete: pd.DataFrame,  # noqa: ARG001
    periodo: str,
    net_expenses: bool,
) -> pd.DataFrame:
    """
    Create a DataFrame with all expenses in a given period.

    The DataFrame should contain the following columns:
        - Date: Date of the expense.
        - Category: Category of the expense.
        - Subcategory: Subcategory of the expense.
        - Payee: Payee of the expense.
        - Narration: Description of the expense.
        - Amount_ars: Amount of the expense in ARS.
        - Amount_usd: Amount of the expense in USD.
        - Tags: tags added to the transactions

    Args:
    ----
        all_expenses_complete (pd.DataFrame): DataFrame with all expenses.
        periodo (str): Period to filter the expenses.
        net_expenses (bool): If True, it will return the net expenses.

    """
    return duckdb.query(
        f"""
    SELECT *
    FROM all_expenses_complete
    WHERE
      EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM '{periodo}'::DATE)
      AND EXTRACT(MONTH FROM Date) = EXTRACT(MONTH FROM '{periodo}'::DATE)
      {"AND NOT array_contains(tags, 'exclude')" if net_expenses else ""}
    ORDER BY date ASC
        """  # noqa: S608
    ).to_df()
