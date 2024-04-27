"""
Create a line chart to display the historic expenses ratios.

The function `expenses_historic_line_chart` creates a line chart to display the historic
expenses ratios.

The DataFrame `source` should have the following columns:
- `x`: the date of the expense.
- `y`: the ratio of the expense.
- `category`: the category of the expense.

The categories should be `RatioBruto` and `RatioNeto`.
"""

import altair as alt
import pandas as pd
import streamlit as st


@st.cache_data
def expenses_historic_cat_chart(source: pd.DataFrame) -> alt.LayerChart:
    """
    Create a line chart to display the historic expenses ratios.

    The DataFrame `source` should have the following columns:
    - `x`: the date of the expense.
    - `y`: the ratio of the expense.
    - `category`: the category of the expense.

    The categories should be `RatioBruto` and `RatioNeto`.

    Args:
    ----
        source (pd.DataFrame): The data to be displayed in the chart.

    """
    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection_point(
        nearest=True,
        on="mouseover",
        fields=["x"],
        empty=False,
    )

    # The basic line
    line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            color=alt.Color(
                "category:N",
                title="Type",
                legend=alt.Legend(
                    orient="top",
                    # legendX=bottom,
                    # titleAlign="center",
                    # titleAnchor="middle",
                    # titleOrient="top",
                    # direction="horizontal",
                ),
            ),
            x=alt.X("x:T", title="Date", axis=alt.Axis(format=("%b %Y"))),
            y=alt.Y("y:Q", title="Ratio (%)", scale=alt.Scale(domain=(0, 100))),
        )
    )

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0))  # type: ignore # noqa: PGH003
    )

    # Draw a rule at the location of the selection
    rules = (
        alt.Chart(source)
        .transform_pivot("category", value="y", groupby=["x"])
        .mark_rule(color="gray")
        .encode(
            x="x:T",
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),  # type: ignore # noqa: PGH003
            tooltip=[
                alt.Tooltip("x:T", title="Date"),
                alt.Tooltip("RatioBruto", type="quantitative", title="Gross Ratio"),
                alt.Tooltip("RatioNeto", type="quantitative", title="Net Ratio"),
            ],
        )
        .add_params(nearest)
    )

    # Put the five layers into a chart and bind the data
    return alt.layer(line, points, rules).properties(
        title="Historic Expenses Ratios",
        height=600,
    )
