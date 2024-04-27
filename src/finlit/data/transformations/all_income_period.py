"""
Create a DataFrame with all expenses in a given period.
"""

import duckdb
import pandas as pd
import streamlit as st


@st.cache_data
def all_income_period(
    all_income_complete: pd.DataFrame,  # noqa: ARG001
    periodo: str,
) -> pd.DataFrame:
    """
    Create a DataFrame with all income in a given period.

    The data frame should contain the following columns:
        - Date: Date of the income.
        - Account: Account of the income.
        - Origin: Origin of the income.
        - Payee: Payee of the income.
        - Narration: Description of the income.
        - Amount_ars: Amount of the income in ARS.
        - Amount_usd: Amount of the income in USD.

    Args:
    ----
        all_income_complete (pd.DataFrame): DataFrame with all income.
        periodo (str): Period to filter the income.

    """
    return duckdb.query(
        f"""
    SELECT *
    FROM all_income_complete
    WHERE
      EXTRACT(YEAR FROM Date) = EXTRACT(YEAR FROM '{periodo}'::DATE)
      AND EXTRACT(MONTH FROM Date) = EXTRACT(MONTH FROM '{periodo}'::DATE)
    ORDER BY date ASC
        """  # noqa: S608
    ).to_df()
