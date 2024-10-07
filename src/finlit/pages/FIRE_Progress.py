"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""  # noqa: N999

from logging import getLogger

import altair as alt
import pandas as pd
import pytz
import streamlit as st
from streamlit.components.v1 import html

from finlit.data import Ledger
from finlit.data.datasets import (
    AllExpensesDataset,
    AllIncomeDataset,
    NetworthHistoryDataset,
    NetworthTrajectoryDataset,
    TrajectoryParams,
)
from finlit.data.transformations import calculate
from finlit.utils import create_parser, format_number, setup_logger, style_css
from finlit.viz.fire_progress import (
    coast_indicator,
    networth_projection,
    networth_summary,
    nw_indicator,
    simple_indicator,
)

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
    }

    .stPlotlyChart {
      display: flex;
      justify-content: center;
      align-items: center;
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

# Income and expenses
all_expenses: pd.DataFrame = AllExpensesDataset(ledger, "all_expenses").build()
all_income: pd.DataFrame = AllIncomeDataset(ledger, "all_income").build()

income = calculate.average_income(all_income, trailing_months)
expenses = calculate.average_expenses(all_expenses, trailing_months)


networth_history = NetworthHistoryDataset(ledger)
bal_df = networth_history.build()
net_worth = bal_df.iloc[-1].net_worth
invested_money = calculate.invested_money(ledger)

test_df = bal_df.copy()
# Filter only the last day of the month. I'm using the 28th as a proxy.
test_df = test_df[(test_df["date"].dt.day == 28)]  # noqa: PLR2004

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
    net_worth_df=bal_df,
)

network_projection = NetworthTrajectoryDataset(ledger, params)

# Coasting fire
network_projection_df = network_projection.build()
coast_projection_df = network_projection.build_coast_fire()

# Contributions
probable_contrib = income - expenses
possible_contrib = income * params.save_rate / 100
# possible_contrib = 3000
conservative_contrib = probable_contrib * 0.75
optimal_contrib = calculate.optimal_contribution(
    net_worth, params.return_rate, params.years, params.dream_total
)


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
    last_year_net_worth = bal_df.iloc[-365].net_worth

    net_worth_indicator = nw_indicator(
        net_worth, last_year_net_worth, "Net Worth", "YoY variation"
    )

    invested_indicator = nw_indicator(
        invested_money, last_year_net_worth, "Invested money", "YoY variation"
    )

    coast_number = calculate.coast_fire(
        params.dream_total, params.return_rate, params.years
    )

    current_coast = net_worth / coast_number * 100
    ly_coast = last_year_net_worth / coast_number * 100
    coast_indicator_fig = coast_indicator(
        current_coast, ly_coast, "Coast FIRE", "Coast FIRE percentage"
    )

    current_fire = net_worth / params.dream_total * 100
    ly_fire = last_year_net_worth / params.dream_total * 100
    fire_indicator_fig = coast_indicator(
        current_fire,
        ly_fire,
        "FIRE",
        "FIRE percentage",
    )

    coast_number_ind = simple_indicator(coast_number, "Coast FIRE number")
    fire_number_ind = simple_indicator(params.dream_total, "FIRE number")

    indics_cols = st.columns(2)

    with indics_cols[0]:
        st.plotly_chart(net_worth_indicator)
        st.plotly_chart(coast_indicator_fig)

    with indics_cols[1]:
        st.plotly_chart(invested_indicator)
        st.plotly_chart(fire_indicator_fig)

    st.plotly_chart(coast_number_ind)
    st.plotly_chart(fire_number_ind)

with networth_cols[1]:
    networth_projection_chart = networth_projection(
        network_projection_df, coast_projection_df
    )
    st.altair_chart(networth_projection_chart, use_container_width=True)  # type: ignore [reportArgumentType]


networth_summary_chart = networth_summary(bal_df)
st.altair_chart(networth_summary_chart, use_container_width=True)  # type: ignore [reportArgumentType]


#######################

# Finish CSS

#######################

html(
    """
<script>
function centerPlotly() {
  // Element streamlit plotly
  element = parent.document.querySelector(".stPlotlyChart");

  if (element) {
    let parent = element.parentElement;
    while (parent) {
      // Find column parent
      if (parent.matches('div[data-testid="stVerticalBlock"]')) {
        // Finding all children that contain the plotly chart
        const children = parent.querySelectorAll(
          'div[data-testid="element-container"]',
        );

        // Centering all children
        children.forEach((child) => {
          child.classList.add("center-content");
        });
        break;
      }
      parent = parent.parentElement;
    }
  }
}

setInterval(centerPlotly, 1000);

</script>
""",
    height=0,
    width=0,
)
