"""
Function that uses Streamlit's caching mechanism.
"""
from dataclasses import dataclass
from typing import Dict, List, NamedTuple

import streamlit as st
from beancount.loader import LoadError, load_file


@dataclass
class Ledger:
    """
    Returns the entries, errors, and options from the ledger file.
    """

    entries: List[NamedTuple]
    errors: List[LoadError]
    options: Dict[str, str]


@st.cache_data()
def get_ledger(ledger_path: str) -> Ledger:
    """
    Cache function that returns a Ledger object from the path.
    """

    entries, errors, options = load_file(ledger_path)
    return Ledger(entries, errors, options)
