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
    expense_historic_ratio,
    expenses_categorized,
    expenses_categorized_historic,
    expenses_monthly_ratios,
    expenses_showcase,
)
from finlit.utils import create_parser, format_number, setup_logger, style_css
from finlit.viz.monthly_expenses import (
    expenses_bar_chart,
    expenses_historic_ratio_chart,
    expenses_pie_chart,
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

    # Date picker
    ## Year
    year_list = list(range(2022, datetime.now(tz=TZ).year + 1))[::-1]
    selected_year = st.selectbox("Select a year", year_list)

    ## Months
    if selected_year == datetime.now(tz=TZ).year:
        # Only show months up to the current month
        month_list = list(range(1, datetime.now(tz=TZ).month + 1))[::-1]
    else:
        month_list = list(range(1, 13))[::-1]
    selected_month = st.selectbox("Select a month", month_list)

    periodo = f"{selected_year}-{selected_month:02d}-01"
    only_net_expenses = st.checkbox("Show net expenses", value=True)

st.title("Monthly Overview")

#######################

# Plots & Functions


#######################

# Dataframes

all_expenses_complete: pd.DataFrame = AllExpensesDataset(ledger, "all_expenses").build()
all_income_complete: pd.DataFrame = AllIncomeDataset(ledger, "all_income").build()

expenses_period = all_expenses_period(all_expenses_complete, periodo, only_net_expenses)
income_period = all_income_period(all_income_complete, periodo)

#########################
###### Dataframes #######
#########################

logger.debug("Calling expenses_categorized")
expenses_per_cat = expenses_categorized(expenses_period)
logger.debug("Returned from expenses_categorized")
logger.debug("Calling expenses_categorized_historic")
expenses_per_cat_historic = expenses_categorized_historic(
    all_expenses_complete, periodo, only_net_expenses
)
logger.debug("Returned from expenses_categorized_historic")

# Filter out historic categories with no expenses in the current period
filtered_categories = expenses_per_cat["category"].unique()
expenses_per_cat_historic = expenses_per_cat_historic[
    expenses_per_cat_historic["category"].isin(filtered_categories)
]
logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
logger.debug(expenses_per_cat_historic)

# Union both dataframes
expenses_per_cat["type"] = "period"
expenses_per_cat_historic["type"] = "historic"
merged_per_cat = pd.concat([expenses_per_cat, expenses_per_cat_historic])
merged_per_cat = merged_per_cat.sort_values("category", ascending=False)

logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
logger.debug(merged_per_cat)

expenses_historic = expenses_monthly_ratios(all_expenses_complete, all_income_complete)
gross_ratio, net_ratio = expense_historic_ratio(
    all_expenses_complete, all_income_complete
)


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
next_month = datetime.strptime(periodo, "%Y-%m-%d").replace(tzinfo=TZ).date().replace(
    day=28
) + timedelta(days=4)
last_day = next_month - timedelta(days=next_month.day)
days_left = (last_day - datetime.now(tz=TZ).date()).days + 1

daily_budget = 0 if days_left <= 0 else left_over / days_left
daily_budget_str = format_number(daily_budget, prefix="$")

max_cat_expense = expenses_per_cat["expenses_usd"].max()

#########################
######## Ratios #########
#########################

# expense_ratio = calculate.net_expense_ratio(expenses_period, income_period)
expense_ratio = round(expenses_usd / income_usd, 2)


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

cols = st.columns(2, gap="large")
with cols[0]:
    subcols = st.columns(2)

    with subcols[0]:
        st.plotly_chart(
            gauge_expense_chart(
                expense_ratio,
                IDEAL_EXPENSE_RATIO,
                CRITICAL_EXPENSE_RATIO,
                f"{'Net' if only_net_expenses else 'Gross'} Expense Ratio",
                height=120,
            ),
            use_container_width=True,
            theme=None,
        )

    with subcols[1]:
        pie_chart = expenses_pie_chart(
            expenses_per_cat,
            upper_limit=max_cat_expense,
            title="Monthly expenses per category",
        )

        st.altair_chart(pie_chart, use_container_width=True)

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

    chartchart = expenses_bar_chart(
        merged_per_cat,
        upper_limit=max_cat_expense,
        title="TESTTEST",
    )

    st.altair_chart(chartchart, use_container_width=True)
    st.altair_chart(chart, use_container_width=True)
    st.altair_chart(chart_historic, use_container_width=True)


with cols[1]:
    st.subheader("All Expenses")

    st.dataframe(
        expenses_showcase(expenses_period),
        use_container_width=True,
        hide_index=True,
        column_order=["Fecha", "Categoria", "Cantidad", "Descripcion"],
        height=800,
    )


st.divider()


st.altair_chart(
    expenses_historic_ratio_chart(expenses_historic, gross_ratio, net_ratio),  # type: ignore # noqa: PGH003
    use_container_width=True,
)
