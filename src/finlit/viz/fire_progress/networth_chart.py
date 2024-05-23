"""
Net worth summary chart.
"""

import logging

import altair as alt
import pandas as pd
import streamlit as st

from finlit.constants import GREEN_COLOR

logger = logging.getLogger()


# @st.cache_data
def networth_summary(source_df: pd.DataFrame) -> alt.LayerChart:
    """
    Create the net worth summary chart.

    I'll comment that I could use balance_df to get the net worth values but the idea is
    to have a day to day net worth valuation. If I get many years of data, I could use
    the balance_df.

    Args:
    ----
        source_df (pd.DataFrame): DataFrame with the net worth projections.
        balance_df (pd.DataFrame): DataFrame with the balance sheet data.

    """

    # Last month of the data
    today = pd.Timestamp.today()
    first_day = pd.Timestamp(today.year, today.month, 1)
    line_color = "#8be9fd"

    # Less than today
    # Filter only the first day of the month
    source_df = source_df[
        (source_df["date"].dt.day == 28) & (source_df["date"] < first_day)
    ]

    nearest = alt.selection_point(
        nearest=True,
        on="mouseover",
        fields=["date"],
        empty=False,
    )

    line = (
        alt.Chart(source_df.reset_index())
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y(
                "networth:Q",
                title="Networth",
                axis=alt.Axis(format="~s"),
                scale=alt.Scale(
                    domain=[
                        source_df["liabilities"].max() * 1.5,
                        source_df["networth"].max() * 1.5,
                    ]
                ),
            ),
            color=alt.value(line_color),
        )
    )

    # This bar has both columns: libilities and assets
    assets_bar = (
        alt.Chart(source_df)
        .mark_bar(width=30)
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("assets:Q", title="Networth", axis=alt.Axis(format="~s")),
            opacity=alt.OpacityValue(0.2),
            color=alt.value(GREEN_COLOR),
        )
    )

    liabilities_bar = (
        alt.Chart(source_df)
        .mark_bar(width=30)
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("liabilities:Q", title="Networth", axis=alt.Axis(format="~s")),
            opacity=alt.OpacityValue(0.2),
            color=alt.value("#ff5555"),
        )
    )

    # Draw line at coast fire value
    ver_rule = (
        alt.Chart(source_df)
        .mark_point()
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("networth:Q", title="Networth", axis=alt.Axis(format="~s")),
            color=alt.value(line_color),  # Specific color for coast fire
            opacity=alt.condition(nearest, alt.value(1), alt.value(0.5)),  # type: ignore # noqa: PGH003
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    type="temporal",
                    title="Date",
                    format=("%b %Y"),
                ),
                alt.Tooltip(
                    "networth:Q",
                    type="quantitative",
                    title="Net worth",
                    format=".2s",
                ),
                alt.Tooltip(
                    "assets:Q",
                    type="quantitative",
                    title="Assets",
                    format=".2s",
                ),
                alt.Tooltip(
                    "liabilities:Q",
                    type="quantitative",
                    title="Liabilities",
                    format=".2s",
                ),
            ],
        )
        .add_params(nearest)
    )

    return alt.layer(liabilities_bar, assets_bar, line, ver_rule)


@st.cache_data
def networth_projection(source: pd.DataFrame, coast_df: pd.DataFrame) -> alt.LayerChart:
    """
    Create the net worth projection chart.

    Args:
    ----
        source (pd.DataFrame): DataFrame with the net worth projections.
        coast_df (pd.DataFrame): DataFrame with the coast fire projections.

    """

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
            color=alt.value(GREEN_COLOR),  # Light green area color
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
                legend=alt.Legend(title="Category", orient="top-left"),
            ),
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("y:Q", title=""),
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
        .mark_rule(color=GREEN_COLOR)
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
        title="Networth possible trajectories",
        height=600,
    )
