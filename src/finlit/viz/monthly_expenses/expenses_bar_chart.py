"""
Create a bar chart to display the expenses per category.

The function `expenses_bar_chart` creates a bar chart to display the expenses per
category.

The DataFrame `data` should have the following columns:
- `category`: the category of the expense.
- `expenses_usd`: the amount of the expense in USD.
- `expenses_ars`: the amount of the expense in ARS.
"""

import logging

import altair as alt
import pandas as pd

logger = logging.getLogger()


# @st.cache_data
def expenses_bar_chart(
    data: pd.DataFrame, *, upper_limit: int = -1, title: str = "Monthly per Category"
) -> alt.Chart:
    """
    Create a bar chart to display the expenses per category.

    DataFrames should have the following columns:
    - `category`: the category of the expense.
    - `expenses_usd`: the amount of the expense in USD.
    - `expenses_ars`: the amount of the expense in ARS.

    Args:
    ----
        data (pd.DataFrame): The data to be displayed in the chart.
        upper_limit (int): The upper limit for the x-axis.
        title (str): The title of the chart.

    """

    ex_usd = "expenses_usd"
    ex_ars = "expenses_ars"
    cat = "category"

    logger.info(data[ex_usd].max())

    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                ex_usd,
                axis=alt.Axis(labelAngle=0),
            ),
            yOffset="type",
            y=alt.Y(
                cat,
                axis=alt.Axis(grid=False),
            ),
            color="type",
            # y=alt.Y(
            #     "type",
            #     title=None,
            #     # sort="y",
            #     axis=alt.Axis(labelLimit=200),
            #     scale=alt.Scale(paddingInner=0.1),
            # ),
            # yOffset="type",
            # x=alt.X(
            #     ex_usd,
            #     title="Test",
            #     # scale=alt.Scale(
            #     #     domain=(0, data[ex_usd].max() if upper_limit <= 0 else upper_limit)
            #     # )
            # ),
            # color=alt.Color(
            #     ex_usd,
            #     scale=alt.Scale(
            #         scheme={
            #             "name": "blues",
            #         },
            #         reverse=True,
            #     ),
            #     legend=None,
            # ),
            tooltip=[
                alt.Tooltip(cat, title="Category"),
                alt.Tooltip(ex_usd, format="$.2f", title="In USD"),
                alt.Tooltip(ex_ars, format="$.2f", title="In ARS"),
            ],
        )
        .properties(title=title)
    )


# @st.cache_data
def expenses_pie_chart(
    data: pd.DataFrame, *, upper_limit: int = -1, title: str = "Monthly per Category"
) -> alt.Chart:
    """
    Create a bar chart to display the expenses per category.

    DataFrames should have the following columns:
    - `category`: the category of the expense.
    - `expenses_usd`: the amount of the expense in USD.
    - `expenses_ars`: the amount of the expense in ARS.

    Args:
    ----
        data (pd.DataFrame): The data to be displayed in the chart.
        upper_limit (int): The upper limit for the x-axis.
        title (str): The title of the chart.

    """

    ex_usd = "expenses_usd"
    ex_ars = "expenses_ars"
    cat = "category"

    return (
        alt.Chart(data)
        .mark_arc()
        .encode(
            theta=alt.Theta(
                ex_usd,
                title=None,
            ),
            order=alt.Order(
                ex_usd,
                sort="descending",
            ),
            color=alt.Color(
                cat,
                legend=None,
                scale=alt.Scale(
                    scheme="tableau20",
                ),
            ),
            tooltip=[
                alt.Tooltip(cat, title="Category"),
                alt.Tooltip(ex_usd, format="$.2f", title="In USD"),
                alt.Tooltip(ex_ars, format="$.2f", title="In ARS"),
            ],
        )
        .properties(title=title)
    )
