from logging import getLogger

import streamlit as st

from finlit.caching import Ledger, get_ledger
from finlit.reports.monthly import create_monthly_report
from finlit.utils import create_parser, setup_logger
from finlit.widgets import month_picker


def main() -> int | None:
    parser = create_parser()
    args = parser.parse_args()
    setup_logger(args.verbose)
    logger = getLogger()

    logger.info("Starting the application.")
    logger.debug("Verbose mode is activated.")
    st.set_page_config(page_title="Monthly Overview", layout="wide")
    st.title("Monthly Overview")

    ledger: Ledger = get_ledger(args.ledger)

    year, month = month_picker(ledger)

    create_monthly_report(ledger, year, month)
