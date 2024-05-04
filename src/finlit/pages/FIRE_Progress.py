"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""  # noqa: N999

from logging import getLogger

import altair as alt
import pandas as pd
import pytz
import streamlit as st
from sqlalchemy import create_engine

from finlit.data import Ledger
from finlit.data.datasets import AllExpensesDataset, AllIncomeDataset
from finlit.data.transformations import TrajectoryParams, calculate
from finlit.data.transformations.networth_projections import NetworthTrajectory
from finlit.utils import create_parser, format_number, setup_logger, style_css

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

# Plots & Functions


def networth_summary(source: pd.DataFrame) -> alt.Chart:
    """
    Create the net worth summary chart.

    Args:
    ----
        source (pd.DataFrame): DataFrame with the net worth projections.

    """
    today = pd.Timestamp.today().normalize()

    source = source.set_index("date")
    # Less than today
    source = source.loc[source.index < today]

    return (
        alt.Chart(source.reset_index())
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("probable_value:Q", title="Networth", axis=alt.Axis(format="~s")),
        )
    )


@st.cache_data
def networth_projection(source: pd.DataFrame, coast_df: pd.DataFrame) -> alt.LayerChart:
    """
    Create the net worth projection chart.

    Args:
    ----
        source (pd.DataFrame): DataFrame with the net worth projections.
        coast_df (pd.DataFrame): DataFrame with the coast fire projections.

    """

    # Add age column
    # # My birthday is on 2024/12/29
    # born = datetime(1998, 12, 29)
    # source["age_at_date"] = source["date"].apply(
    #     lambda today: float(
    #   today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    #     )
    # )
    # Merge source and coast_df on 'date'
    merged = source.merge(coast_df, on="date", how="left")

    # Create a selection that chooses the nearest point & selects based on x-value
    source = source.set_index("date")
    source = source.reset_index().melt("date", var_name="category", value_name="y")

    # Chart for the coast fire projection data
    coast_line = (
        alt.Chart(coast_df)
        .mark_line(opacity=0.5, strokeDash=[10, 5])
        .encode(
            x="date:T",
            y="coast_value:Q",
            color=alt.value("#2ca02c"),  # Specific color for coast fire
        )
    )

    # Green tinted area under the coast fire projection line
    coast_area = (
        alt.Chart(coast_df)
        .mark_area(opacity=0.2)
        .encode(
            x="date:T",
            y="coast_value:Q",
            color=alt.value("lightgreen"),  # Light green area color
        )
    )

    # Combine the area chart with the line chart
    coast_chart = alt.layer(coast_line, coast_area)

    nearest = alt.selection_point(
        nearest=True,
        on="mouseover",
        fields=["date"],
        empty=False,
    )

    color_domain = [
        "conservative_value",
        "probable_value",
        "possible_value",
        "optimal_value",
    ]
    # Dracula color palette
    color_range = ["#FFB86C", "#FF79C6", "#BD93F9", "#8BE9FD"]

    # The basic line
    line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            color=alt.Color(
                "category:N",
                title="Category",
                scale=alt.Scale(domain=color_domain, range=color_range),
                # scale=alt.Scale(scheme="dark2"),
            ),
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("y:Q"),
        )
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))  # type: ignore # noqa: PGH003
    )

    # Draw line at coast fire value
    coast_rule = (
        alt.Chart(merged)
        # .transform_pivot("category", value="y", groupby=["date"])
        .mark_rule(color="green")
        .encode(
            x="date:T",
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),  # type: ignore # noqa: PGH003
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    type="temporal",
                    title="Date",
                    format=("%b %Y"),
                ),
                alt.Tooltip(
                    "age",
                    type="quantitative",
                    title="Age",
                ),
                alt.Tooltip(
                    "coast_value",
                    type="quantitative",
                    title="Coast Value",
                    format=".2s",
                ),
                alt.Tooltip(
                    "conservative_value",
                    type="quantitative",
                    title="Conservative Value",
                    format=".2s",
                ),
                alt.Tooltip(
                    "probable_value",
                    type="quantitative",
                    title="Probable Value",
                    format=".2s",
                ),
                alt.Tooltip(
                    "optimal_value",
                    type="quantitative",
                    title="Optimal Value",
                    format=".2s",
                ),
                alt.Tooltip(
                    "possible_value",
                    type="quantitative",
                    title="Possible Value",
                    format=".2s",
                ),
            ],
        )
        .add_params(nearest)
    )

    # Put all the layers into a chart and bind the data
    return alt.layer(coast_chart, line, points, coast_rule).properties(
        title="Net worth possible trajectories",
        height=600,
    )


#######################

# Dataframes

#######################

cols = st.columns([1, 2], gap="large")

st.subheader("Summary")

dummy = create_engine("postgresql://postgres:postgres@localhost:5432/finances")


all_expenses: pd.DataFrame = AllExpensesDataset(ledger, dummy, "all_expenses").build()
all_income: pd.DataFrame = AllIncomeDataset(ledger, dummy, "all_income").build()

income = calculate.average_income(all_income, trailing_months)
expenses = calculate.average_expenses(all_expenses, trailing_months)
net_worth = calculate.net_worth(ledger)

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

logger.info("Net worth: %s", net_worth)


network_projection = NetworthTrajectory(ledger, params)

network_projection_df = network_projection.build()

coast_projection_df = network_projection.build_coast_fire()

probable_contrib = income - expenses
possible_contrib = income * params.save_rate / 100
conservative_contrib = probable_contrib * 0.75
optimal_contrib = calculate.optimal_contribution(
    net_worth, params.return_rate, params.years, params.dream_total
)

#######################

# Layout

#######################

metrics_cols = st.columns(4)

st.write("The following contributions are calculated based on the last 6 months.")

metrics_cols[0].metric("Possible Contribution", format_number(possible_contrib))
metrics_cols[1].metric("Probable Contribution", format_number(probable_contrib))
metrics_cols[2].metric("Conservative Contribution", format_number(conservative_contrib))
metrics_cols[3].metric("Optimal Contribution", format_number(optimal_contrib))


networth_projection_chart = networth_projection(
    network_projection_df, coast_projection_df
)
st.altair_chart(networth_projection_chart, use_container_width=True)  # type: ignore [reportArgumentType]

networth_summary_chart = networth_summary(network_projection_df)
st.altair_chart(networth_summary_chart, use_container_width=True)

