"""
Create a gauge chart to display the expense ratio.

The function `gauge_expense_chart` creates a gauge chart to display the expense ratio.
"""

import plotly.graph_objects as go
import streamlit as st


@st.cache_data
def gauge_expense_chart(
    expense_ratio: float,
    ideal_expense_ratio: float,
    critical_expense_ratio: float,
    title: str,
    *,
    height: int = 350,
) -> go.Figure:
    """
    Create a gauge chart to display the expense ratio.

    Args:
    ----
        expense_ratio (float): The expense ratio.
        ideal_expense_ratio (float): The ideal expense ratio.
        critical_expense_ratio (float): The critical expense ratio.
        title (str): The title of the chart.

    """

    fig = go.Figure(layout=go.Layout(height=height, margin={"t": 0, "b": 0}))

    ideal_porcentage = ideal_expense_ratio * 100
    critical_porcentage = critical_expense_ratio * 100
    expense_porcentage = round(expense_ratio * 100, 2)

    bg_ideal_color = "#194226"
    bg_warning_color = "#423a19"
    bg_critical_color = "#42191c"

    fg_ideal_color = "#3fa660"
    fg_warning_color = "#a6933f"
    fg_critical_color = "#a63f47"

    bar_color: str
    if expense_ratio < ideal_expense_ratio:
        bar_color = fg_ideal_color
    elif expense_ratio < critical_expense_ratio:
        bar_color = fg_warning_color
    else:
        bar_color = fg_critical_color

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=expense_porcentage,
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {
                    "range": [None, 100],
                    "tickwidth": 1,
                    "tickcolor": "black",
                },
                "bar": {"color": bar_color, "thickness": 0.75},
                "steps": [
                    {
                        "range": [0, ideal_porcentage],
                        "color": bg_ideal_color,
                        "thickness": 0.75,
                    },
                    {
                        "range": [
                            ideal_porcentage,
                            critical_porcentage,
                        ],
                        "color": bg_warning_color,
                        "thickness": 0.75,
                    },
                    {
                        "range": [critical_porcentage, 100],
                        "color": bg_critical_color,
                        "thickness": 0.75,
                    },
                ],
            },
        )
    )

    # Add white background to figure
    fig.update_layout(title=title, title_y=0)
    # Reduce margins and padding
    fig.update_layout(margin={"t": 0, "b": 0, "l": 0, "r": 0})

    return fig
