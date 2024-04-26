"""
Function that uses Streamlit's caching mechanism.
"""

import streamlit as st
from pgloader.ledger import Ledger


@st.cache_data()
def get_ledger(ledger_path: str) -> Ledger:
    """
    Cache function that returns a Ledger object from the path.
    """

    return Ledger(ledger_path)
