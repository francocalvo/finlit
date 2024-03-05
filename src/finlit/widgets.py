"""
Widget functions for the streamlit app.
"""

import calendar
from typing import Tuple

import pandas as pd
import streamlit as st
from beancount.query.query import run_query

from finlit.caching import Ledger


def month_picker(ledger: Ledger) -> Tuple[int, int]:
    """
    Create a month picker widget.
    """

    query = "SELECT YEAR, MAX(MONTH) AS MONTH GROUP BY YEAR"
    _, result_raw = run_query(ledger.entries, ledger.options, query)

    df_result = pd.DataFrame(result_raw)

    date_ops = {}
    for _, row in df_result.iterrows():
        date_ops[row["year"]] = [
            calendar.month_name[i] for i in range(1, row["month"] + 1)
        ]

    year_ops: None | str = st.sidebar.selectbox("Select year", date_ops)
    month_ops: None | str = st.sidebar.selectbox("Select month", date_ops[year_ops])

    # Convert the month name to its number
    month_ops = str(date_ops[year_ops].index(month_ops) + 1)
    year_ops = str(year_ops)

    return int(year_ops), int(month_ops)
