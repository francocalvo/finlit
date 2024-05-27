"""
Create a bar chart to display the portfolio holdings per asset.
"""

import logging

import altair as alt
import pandas as pd

logger = logging.getLogger()


def holdings_chart(
    data: pd.DataFrame,
    title: str = "Holdings",
    *,
    subportfolio: bool = False,
    tags: bool = False,
) -> alt.Chart | alt.LayerChart:
    """
    Create a bar chart to display the expenses per category.

    DataFrames should have the following columns:
    - `ticker`: the ticker of the asset.
    - `asset_class`: the asset class.
    - `name`: the name of the asset.
    - `value`: the value of the asset.

    Args:
    ----
        data (pd.DataFrame): The data to be displayed in the chart.
        title (str): The title of the chart.
        subportfolio (bool): Whether the chart is for a subportfolio.
        tags (bool): Whether to display tags in the tooltip.

    """

    basic_tooltip = [
        alt.Tooltip("name", title="Name"),
        alt.Tooltip("asset_class", title="Asset Class"),
        alt.Tooltip("value", format="$.2f", title="Value (USD)"),
    ]
    if not subportfolio:
        basic_tooltip.insert(3, alt.Tooltip("portfolio", title="Portfolio"))

    base = (
        alt.Chart(data)
        .encode(
            theta=alt.Theta(
                "value",
                title=None,
                stack=True,
            ),
            order=alt.Order(
                ["asset_class", "value"] if subportfolio else "value",
                sort="descending",
            ),
            color=alt.Color(
                "name",
                legend=None,
            ),
            tooltip=basic_tooltip,
        )
        .properties(height=290)
    )

    pie = base.mark_arc(outerRadius=100).properties(
        title=alt.TitleParams(
            title,
            anchor="middle",
            dy=20,
        )
    )

    text = base.mark_text(radius=120).encode(
        text="ticker:N",
    )

    padding = {"left": 0, "top": 150, "right": 0, "bottom": 0}
    if tags:
        result = pie + text
        result.properties(padding=padding)
        return result
    return pie.properties(padding=padding)
