"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""  # noqa: N999

from logging import getLogger

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
from sqlalchemy import create_engine
from streamlit.components.v1 import html

from finlit.data import Ledger
from finlit.data.datasets import AllExpensesDataset, AllIncomeDataset, BalanceDataset
from finlit.data.transformations import TrajectoryParams, calculate
from finlit.data.transformations.networth_projections import NetworthTrajectory
from finlit.utils import create_parser, format_number, setup_logger, style_css
from finlit.viz.fire_progress import networth_projection, networth_summary

tz = pytz.timezone("America/Argentina/Cordoba")

st.set_page_config(
    page_title="Personal Finances Dashboard",
    page_icon="🏂",
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


#######################
# Page configuration

alt.themes.enable("dark")

#######################
# CSS styling

st.markdown(style_css, unsafe_allow_html=True)

# Center in div all objects with class stPlotlyChart
# and the parent div
st.markdown(
    """
  <style>
    .center-content {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column; /* Or 'row' depending on your needs */
      height: 100%; /* Ensure the parent takes up full height */
    }
  </style>
    """,
    unsafe_allow_html=True,
)

#######################
# Sidebar

with st.sidebar:
    st.title("Monthly Expenses")

    swr = st.number_input(
        "Safe Withdrawal Rate (%)", min_value=0.0, max_value=10.0, value=3.5
    )

    expected_monthly_expenses = st.number_input(
        "Expected Monthly Expenses", min_value=0.0, value=5000.0
    )

    years_to_retire = int(st.number_input("Years to Retire", min_value=0, value=30))

    rate_of_return = st.number_input(
        "Rate of Return (%)", min_value=0.0, max_value=100.0, value=5.5
    )

    save_rate = st.number_input(
        "Save Rate (%)", min_value=0.0, max_value=100.0, value=75.0
    )

trailing_months: int = 6
st.title("FIRE Progress")

#######################

# Dataframes

#######################

cols = st.columns([1, 2], gap="large")

st.subheader("Summary")

dummy = create_engine("postgresql://postgres:postgres@localhost:5432/finances")


# Income and expenses
all_expenses: pd.DataFrame = AllExpensesDataset(ledger, dummy, "all_expenses").build()
all_income: pd.DataFrame = AllIncomeDataset(ledger, dummy, "all_income").build()

income = calculate.average_income(all_income, trailing_months)
expenses = calculate.average_expenses(all_expenses, trailing_months)

# Balance sheet and net worth
bal = BalanceDataset(ledger, dummy, "balance")
bal_df = bal.build()
net_worth = calculate.net_worth(ledger)

# Trajectory parameters
params = TrajectoryParams(
    return_rate=rate_of_return / 100,
    swr=swr,
    dream=expected_monthly_expenses,
    years=years_to_retire,
    save_rate=save_rate,
    trailing_months=trailing_months,
    income=income,
    expenses=expenses,
    net_worth=net_worth,
)

logger.debug("Networth: %s", net_worth)

network_projection = NetworthTrajectory(ledger, params)

# Coasting fire
network_projection_df = network_projection.build()
coast_projection_df = network_projection.build_coast_fire()


# Contributions
probable_contrib = income - expenses
possible_contrib = income * params.save_rate / 100
conservative_contrib = probable_contrib * 0.75
optimal_contrib = calculate.optimal_contribution(
    net_worth, params.return_rate, params.years, params.dream_total
)


def coast_indicator(
    value: float, reference: float, title: str, subtitle: str | None = None
) -> go.Figure:
    title_text = (
        title
        if not subtitle
        else f"{title}<br><span style='font-size:0.8em;color:gray'>{subtitle}</span>"
    )

    return go.Figure(
        go.Indicator(
            mode="number+delta",
            value=value,
            number={"suffix": "%"},
            delta={
                "reference": reference,
                "position": "bottom",
                "valueformat": ".2%",
                "relative": True,
            },
            title={"text": title_text},
        )
    ).update_layout(width=150, height=150, margin={"t": 50, "b": 0, "l": 10, "r": 10})


def nw_indicator(
    value: float,
    reference: float,
    title: str,
    subtitle: str | None = None,
) -> go.Figure:
    title_text = (
        title
        if not subtitle
        else f"{title}<br><span style='font-size:0.8em;color:gray'>{subtitle}</span>"
    )
    return go.Figure(
        go.Indicator(
            mode="number+delta",
            value=value,
            number={"prefix": "$"},
            delta={
                "reference": reference,
                "position": "bottom",
                "valueformat": ".2%",
                "relative": True,
            },
            title={"text": title_text},
        )
    ).update_layout(width=150, height=150, margin={"t": 50, "b": 0, "l": 10, "r": 10})


#######################

# Layout

#######################


metrics_cols = st.columns(4)

st.write("The contributions are calculated based on the last 6 months.")


metrics_cols[0].metric("Possible Contribution", format_number(possible_contrib))
metrics_cols[1].metric("Probable Contribution", format_number(probable_contrib))
metrics_cols[2].metric("Conservative Contribution", format_number(conservative_contrib))
metrics_cols[3].metric("Optimal Contribution", format_number(optimal_contrib))


networth_cols = st.columns([1, 3])

with networth_cols[0]:
    last_year_net_worth = bal_df.iloc[-13].net_worth
    logger.debug("Last year net worth: %s", last_year_net_worth)

    net_worth_indicator = nw_indicator(
        net_worth, last_year_net_worth, "Net Worth", "YoY variation"
    )

    coast_number = calculate.coast_fire(
        params.dream_total, params.return_rate, params.years
    )
    current_coast = net_worth / coast_number * 100

    coast_indicator_fig = coast_indicator(
        current_coast, 100, "Coast FIRE", "Coast FIRE percentage"
    )

    st.plotly_chart(net_worth_indicator)
    st.plotly_chart(coast_indicator_fig)


with networth_cols[1]:
    networth_projection_chart = networth_projection(
        network_projection_df, coast_projection_df
    )
    st.altair_chart(networth_projection_chart, use_container_width=True)  # type: ignore [reportArgumentType]


networth_summary_chart = networth_summary(network_projection_df, bal_df)
st.altair_chart(networth_summary_chart, use_container_width=True)  # type: ignore [reportArgumentType]


html(
    """
<script>
console.log("HEEEEEEEREEEEE")
// wait 2 seconds 
setTimeout(addCenterContentClass, 1);
console.log("Waiting 2 seconds")

// define fn
function addCenterContentClass() {
  console.log("Adding center-content class");
  element = parent.document.querySelector('.stPlotlyChart')
  console.log(element);
  if (element) {
    let parent = element.parentElement;
    while (parent) {
      console.log(parent);
      if (parent.matches('div[data-testid="column"]')) {
        // Add the center-content class to the parent element
        console.log("Adding center-content class to parent");
        parent.classList.add('center-content');
        break;
      }
      parent = parent.parentElement;
    }
  }
}
</script>
""",
    height=0,
    width=0,
)
