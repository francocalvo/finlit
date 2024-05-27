"""
Net worth summary chart.
"""

import logging

import altair as alt
import pandas as pd

from finlit.constants import CYAN_COLOR, GREEN_COLOR, RED_COLOR

logger = logging.getLogger()


# @st.cache_data
def networth_chart(
    all_df: pd.DataFrame,
    global_df: pd.DataFrame,
    argy_df: pd.DataFrame,
) -> alt.LayerChart:
    """
    Create the net worth summary chart.

    I'll comment that I could use balance_df to get the net worth values but the idea is
    to have a day to day net worth valuation. If I get many years of data, I could use
    the balance_df.

    Args:
    ----
        all_df (pd.DataFrame): DataFrame with the net worth projections.
        balance_df (pd.DataFrame): DataFrame with the balance sheet data.

    """

    # Last month of the data
    today = pd.Timestamp.today()
    line_color = CYAN_COLOR

    # Less than today
    # Filter only the first day of the month
    all_df = all_df[(all_df["date"] < today)]
    global_df = global_df[(global_df["date"] < today)]
    argy_df = argy_df[(argy_df["date"] < today)]

    merged_df = all_df.merge(global_df, on="date", how="left", suffixes=("", "_global"))
    merged_df = merged_df.merge(argy_df, on="date", how="left", suffixes=("", "_argy"))
    merged_df = merged_df.filter(
        ["date", "net_worth", "net_worth_global", "net_worth_argy"]
    )

    nearest = alt.selection_point(
        nearest=True,
        on="mouseover",
        fields=["date"],
        empty=False,
    )

    line = (
        alt.Chart(merged_df)
        .mark_line(interpolate="basis")
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y(
                "net_worth:Q",
                title="Net worth",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.value(RED_COLOR),
        )
    ).properties(height=800)

    line_argy = (
        alt.Chart(merged_df)
        .mark_line(interpolate="basis")
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y(
                "net_worth_argy:Q",
                title="Net worth",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.value(CYAN_COLOR),
        )
    ).properties(height=800)

    line_global = (
        alt.Chart(merged_df)
        .mark_line(interpolate="basis")
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y(
                "net_worth_global:Q",
                title="Net worth",
                axis=alt.Axis(format="~s"),
            ),
            color=alt.value(GREEN_COLOR),
        )
    ).properties(height=800)

    # Draw line at coast fire value
    ver_rule = (
        alt.Chart(merged_df)
        .mark_point()
        .encode(
            x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("net_worth:Q", title="Net worth", axis=alt.Axis(format="~s")),
            color=alt.value(line_color),  # Specific color for coast fire
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),  # type: ignore # noqa: PGH003
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    type="temporal",
                    title="Date",
                    format=("%d %b %Y"),
                ),
                alt.Tooltip(
                    "net_worth:Q",
                    type="quantitative",
                    title="Invested",
                    format=".2s",
                ),
                alt.Tooltip(
                    "net_worth_argy:Q",
                    type="quantitative",
                    title="Invested in Argentina",
                    format=".2s",
                ),
                alt.Tooltip(
                    "net_worth_global:Q",
                    type="quantitative",
                    title="Invested in Global",
                    format=".2s",
                ),
            ],
        )
        .add_params(nearest)
    )

    return alt.layer(line, line_argy, line_global, ver_rule)
