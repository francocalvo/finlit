"""
Net worth summary chart.
"""

import logging
from dataclasses import dataclass
from typing import List

import altair as alt
import pandas as pd
import streamlit as st

from finlit.constants import CYAN_COLOR, RED_COLOR

logger = logging.getLogger()


@dataclass
class NetworthSubset:
    name: str
    df: pd.DataFrame
    color: str


# @st.cache_data
def networth_chart(
    all_df: pd.DataFrame,
    subsets: List[NetworthSubset],
) -> alt.LayerChart:
    """
    Create the net worth summary chart.

    I'll comment that I could use balance_df to get the net worth values but the idea is
    to have a day to day net worth valuation. If I get many years of data, I could use
    the balance_df.

    Args:
    ----
        all_df (pd.DataFrame): DataFrame with the net worth projections.
        subsets (list[NetworthSubset]): List of NetworthSubset with the net worth projections.

    """
    # Last month of the data
    today = pd.Timestamp.today()
    line_color = CYAN_COLOR

    # Less than today
    # Filter only the first day of the month
    all_df = all_df[(all_df["date"] < today)]
    for subset in subsets:
        subset.df = subset.df[(subset.df["date"] < today)]

    # for subset in subsets:
    #     st.write(subset.name)
    #     st.write(subset.df)

    merged_df = all_df.filter(["date", "net_worth"])
    for subset in subsets:
        merged_df = merged_df.merge(
            subset.df, on="date", how="left", suffixes=("", f"_{subset.name}")
        )

    st.write(merged_df)

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

    lines = [line]

    for subset in subsets:
        line = (
            alt.Chart(merged_df)
            .mark_line(interpolate="basis")
            .encode(
                x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
                y=alt.Y(
                    f"net_worth_{subset.name}:Q",
                    title="Net worth",
                    axis=alt.Axis(format="~s"),
                ),
                color=alt.value(subset.color),
            )
        ).properties(height=800)

        lines.append(line)

    # Draw line at coast fire value
    ver_rule = (
        alt.Chart(merged_df)
        .mark_rule()
        .encode(
            # x=alt.X("date:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            x="date:T",
            # y=alt.Y("net_worth:Q", title="Net worth", axis=alt.Axis(format="~s")),
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
            ]
            + [
                alt.Tooltip(
                    f"net_worth_{subset.name}:Q",
                    type="quantitative",
                    title=f"Invested in {subset.name.capitalize()}",
                    format=".2s",
                )
                for subset in subsets
            ],
        )
        .add_params(nearest)
    )

    return alt.layer(line, ver_rule, *lines)
