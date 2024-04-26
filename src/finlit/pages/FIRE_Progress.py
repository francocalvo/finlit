"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""

from datetime import datetime
from logging import getLogger

import altair as alt
import pytz
import streamlit as st
from pandas import DataFrame
from sqlalchemy import create_engine

from finlit.caching import Ledger, get_ledger
from finlit.data.datasets import NetworthTrajectory
from finlit.utils import create_parser, setup_logger

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
ledger: Ledger = get_ledger(args.ledger)


#######################
# Page configuration

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown(
    """
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

</style>
""",
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

st.title("FIRE Progress")

#######################

# Plots & Functions


def format_number(num: float, *, prefix: str = "", posfix: str = "") -> str:
    million = 1000000
    thousand = 1000
    formatted = f"{num:.2f}"
    if num > million:
        formatted = (
            f"{num // million} M"
            if not num % million
            else f"{round(num / million, 1)} M"
        )
    if num > thousand * 100:
        formatted = (
            f"{num // thousand} K"
            if not num % thousand
            else f"{round(num / thousand, 1)} K"
        )

    return f"{prefix}{formatted}{posfix}"


def networth_summary(source: DataFrame) -> alt.Chart:
    today = datetime.now(tz=tz).date()

    source = source.set_index("date")
    # Less than today
    source = source.loc[source.index < today]

    chart = (
        alt.Chart(source.reset_index())
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("probable_value:Q", title="Networth", axis=alt.Axis(format="~s")),
        )
    )

    return chart


def networth_projection(source: DataFrame) -> alt.LayerChart:
    # Create a selection that chooses the nearest point & selects based on x-value

    source = source.set_index("date")
    source = source.reset_index().melt("date", var_name="category", value_name="y")

    logger.info("Columns: %s", source.columns)
    logger.info("Data:")
    logger.info(source)

    columns = [
        "conservative_value",
        "probable_value",
        "optimal_value",
        "possible_value",
    ]
    logger.info("Columns: %s", columns)

    nearest = alt.selection_point(
        nearest=True,
        on="mouseover",
        fields=["date"],
        empty=False,
    )

    # The basic line
    line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            color=alt.Color("category:N", title="Category"),
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("y:Q"),
        )
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))  # type: ignore # noqa: PGH003
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(source)
        .transform_pivot("category", value="y", groupby=["date"])
        .mark_rule(color="gray")
        .encode(
            x="date:T",
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),  # type: ignore # noqa: PGH003
            tooltip=[
                alt.Tooltip(
                    "conservative_value",
                    type="quantitative",
                    title="Conservative Value",
                    format=".2f",
                ),
                alt.Tooltip(
                    "probable_value",
                    type="quantitative",
                    title="Probable Value",
                    format=".2f",
                ),
                alt.Tooltip(
                    "optimal_value",
                    type="quantitative",
                    title="Optimal Value",
                    format=".2f",
                ),
                alt.Tooltip(
                    "possible_value",
                    type="quantitative",
                    title="Possible Value",
                    format=".2f",
                ),
            ],
        )
        .add_params(nearest)
    )

    # Put the five layers into a chart and bind the data
    return alt.layer(line, points, rules).properties(
        title="Historic Expenses Ratios",
        height=600,
    )


#######################

# Dataframes

#######################
# Layout


cols = st.columns([1, 2], gap="large")

st.subheader("Summary")
network_projection_df = NetworthTrajectory(
    ledger,
    engine,
    interest_rate=rate_of_return / 100,
    swr=swr,
    dream=expected_monthly_expenses,
    years=years_to_retire,
    save_rate=save_rate,
).build()

networth_projection_chart = networth_projection(network_projection_df)
st.altair_chart(networth_projection_chart, use_container_width=True)  # type: ignore [reportArgumentType]

networth_summary_chart = networth_summary(network_projection_df)
st.altair_chart(networth_summary_chart, use_container_width=True)


with cols[1]:
    pass
