"""
Create a DataFrame with all expenses with categories and subcategories.
"""

import duckdb
import pandas as pd
import streamlit as st


@st.cache_data
def expenses_showcase(
    all_expenses_complete: pd.DataFrame,  # noqa: ARG001
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
        all_expenses_complete (pd.DataFrame): DataFrame with all expenses.

    """
    return duckdb.query(
        """
    SELECT
     Date AS Fecha,
      CONCAT(Category, ' ⟶ ', Subcategory) AS Categoria,
      Narration AS Descripcion,
      Amount_usd AS Cantidad
    FROM all_expenses_complete
    ORDER BY date ASC
        """
    ).to_df()
