"""
Finlit - Personal Finances Dashboard.
"""  # noqa: N999

from datetime import datetime, timedelta
from logging import getLogger

import altair as alt
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

from finlit.constants import TZ
from finlit.data.datasets import AllExpensesDataset, AllIncomeDataset
from finlit.data.ledger import Ledger
from finlit.data.transformations import (
    all_expenses_period,
    all_income_period,
    calculate,
    expenses_categorized,
    expenses_categorized_historic,
    expenses_historic_ratios,
    expenses_showcase,
)
from finlit.utils import create_parser, format_number, setup_logger, style_css
from finlit.viz.monthly_expenses import (
    expenses_bar_chart,
    expenses_historic_cat_chart,
    gauge_expense_chart,
)

st.set_page_config(
    page_title="Personal Finances Dashboard",
    page_icon="./assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

parser = create_parser()
args = parser.parse_args()
setup_logger(verbose=args.verbose)
logger = getLogger()

logger.info("Starting the application.")
logger.debug("Verbose mode is activated.")
ledger = Ledger(args.ledger)


IDEAL_EXPENSE_RATIO = 0.25
CRITICAL_EXPENSE_RATIO = 0.5


#######################
# Page configuration

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown(
    style_css,
    unsafe_allow_html=True,
)


#######################
# Load data

## Dummy db connection
engine = create_engine("postgresql://postgres:postgres@localhost:5432/finances")

#######################
# Sidebar

with st.sidebar:
    st.title("Monthly Expenses")

    year_list = list(range(2022, datetime.now(tz=TZ).year + 1))[::-1]
    selected_year = st.selectbox("Select a year", year_list)

    if selected_year == datetime.now(tz=TZ).year:
        # Only show months up to the current month
        month_list = list(range(1, datetime.now(tz=TZ).month + 1))[::-1]
    else:
        month_list = list(range(1, 13))[::-1]

    selected_month = st.selectbox("Select a month", month_list)

    logger.info("Selected year: %s", selected_year)
    logger.info("Selected month: %s", selected_month)
    periodo = f"{selected_year}-{selected_month:02d}-01"

    logger.info("Selected period: %s", periodo)

st.title("Monthly Overview")

#######################

# Plots & Functions


#######################

# Dataframes

all_expenses_complete: pd.DataFrame = AllExpensesDataset(
    ledger, engine, "all_expenses"
).build()
all_income_complete: pd.DataFrame = AllIncomeDataset(
    ledger, engine, "all_income"
).build()

expenses_period = all_expenses_period(all_expenses_complete, periodo)
income_period = all_income_period(all_income_complete, periodo)


#########################
###### Dataframes #######
#########################

expenses_per_cat = expenses_categorized(expenses_period)
expenses_per_cat_historic = expenses_categorized_historic(
    all_expenses_complete, periodo
)
expenses_historic = expenses_historic_ratios(all_expenses_complete, all_income_complete)


#########################
##### Scalar values #####
#########################

expenses_ars = calculate.sum_field(expenses_period, "Amount_Ars")
expenses_usd = calculate.sum_field(expenses_period, "Amount_Usd")
income_ars = calculate.sum_field(income_period, "Amount_Ars")
income_usd = calculate.sum_field(income_period, "Amount_Usd")

expenses_ars_str = format_number(expenses_ars, prefix="$")
expenses_usd_str = format_number(expenses_usd, posfix=" USD")
income_ars_str = format_number(income_ars, prefix="$")
income_usd_str = format_number(income_usd, posfix=" USD")

left_over = (income_ars * IDEAL_EXPENSE_RATIO) - expenses_ars
left_over_str = format_number(left_over, prefix="$")

# Calculate days left from today to the end of the month of periodo
next_month = datetime.strptime(periodo, "%Y-%m-%d").replace(tzinfo=TZ) + timedelta(
    days=30
)
last_day = next_month - timedelta(days=next_month.day)
days_left = (last_day - datetime.now(tz=TZ)).days
daily_budget = 0 if days_left < 0 else left_over / days_left
daily_budget_str = format_number(daily_budget, prefix="$")

max_cat_expense = expenses_per_cat["expenses_usd"].max()

#########################
######## Ratios #########
#########################

net_expense_ratio = calculate.net_expense_ratio(expenses_period, income_period)
gross_expense_ratio = round(expenses_usd / income_usd, 2)


#######################
# Layout

st.subheader("Summary")

metric_cols = st.columns(6)
metric_cols[0].metric(label="Total Income (ARS)", value=income_ars_str)
metric_cols[1].metric(label="Total Income (USD)", value=income_usd_str)
metric_cols[2].metric(label="Total Expenses (ARS)", value=expenses_ars_str)
metric_cols[3].metric(label="Total Expenses (USD)", value=expenses_usd_str)
metric_cols[4].metric(label="Ideal Left Over", value=left_over_str)
metric_cols[5].metric(label="Ideal Daily Budget", value=daily_budget_str)

st.divider()

cols = st.columns([1, 2], gap="large")
with cols[0]:
    st.plotly_chart(
        gauge_expense_chart(
            net_expense_ratio,
            IDEAL_EXPENSE_RATIO,
            CRITICAL_EXPENSE_RATIO,
            "Net Expense Ratio",
            height=250,
        ),
        use_container_width=True,
        theme=None,
    )

    st.plotly_chart(
        gauge_expense_chart(
            gross_expense_ratio,
            IDEAL_EXPENSE_RATIO,
            CRITICAL_EXPENSE_RATIO,
            "Gross Expense Ratio",
            height=250,
        ),
        use_container_width=True,
        theme=None,
    )


with cols[1]:
    st.subheader("All Expenses")

    logger.info("All expenses: %s", expenses_period)

    st.dataframe(
        expenses_showcase(expenses_period),
        use_container_width=True,
        hide_index=True,
        column_order=["Fecha", "Categoria", "Cantidad", "Descripcion"],
        height=450,
    )


st.divider()


chart = expenses_bar_chart(
    expenses_per_cat,
    upper_limit=max_cat_expense,
    title="Monthly expenses per category",
)
chart_historic = expenses_bar_chart(
    expenses_per_cat_historic,
    upper_limit=max_cat_expense,
    title="Historic monthly expenses per category",
)

expenses_cols = st.columns(2, gap="large")
expenses_cols[0].altair_chart(chart, use_container_width=True)
expenses_cols[1].altair_chart(chart_historic, use_container_width=True)

st.altair_chart(
    expenses_historic_cat_chart(expenses_historic),  # type: ignore # noqa: PGH003
    use_container_width=True,
)
