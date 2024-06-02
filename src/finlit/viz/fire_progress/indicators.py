"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""

import plotly.graph_objects as go
import pytz

tz = pytz.timezone("America/Argentina/Cordoba")


def coast_indicator(
    value: float, reference: float, title: str, subtitle: str | None = None
) -> go.Figure:
    """
    Create a indicator plot for Coast FIRE and FIRE.
    """
    title_text = (
        title
        if not subtitle
        else f"""<span style='margin-bottom:2cm;font-size:1rem;font-weight:bold;'>{title}</span><br><br><span style='margin-top:2cm;font-size:0.8rem;color:gray'>{subtitle}</span>"""  # noqa: E501
    )

    return go.Figure(
        go.Indicator(
            mode="number+delta",
            value=round(value, 2),
            number={
                "suffix": "%",
                "font": {
                    "size": 35,
                },
            },
            delta={
                "reference": reference,
                "position": "bottom",
                "valueformat": ".2",
                "suffix": "%",
            },
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title_text},
        )
    ).update_layout(width=120, height=110, margin={"t": 50, "b": 0, "l": 10, "r": 10})


def nw_indicator(
    value: float,
    reference: float,
    title: str,
    subtitle: str | None = None,
) -> go.Figure:
    """
    Create a indicator plot for Net Worth-like metrics.

    Args:
    ----
        value (float): Current value.
        reference (float): Reference value.
        title (str): Title of the indicator.
        subtitle (str | None): Subtitle of the indicator.

    """
    title_text = (
        title
        if not subtitle
        else f"""<span style='margin-bottom:2cm;font-size:1rem;font-weight:bold;'>{title}</span><br><br><span style='margin-top:2cm;font-size:0.8rem;color:gray'>{subtitle}</span>"""  # noqa: E501
    )
    return go.Figure(
        go.Indicator(
            mode="number+delta",
            value=value,
            number={
                "prefix": "$",
                "font": {
                    "size": 35,
                },
            },
            delta={
                "reference": reference,
                "position": "bottom",
                "valueformat": ".2%",
                "relative": True,
            },
            title={
                "text": title_text,
            },
        )
    ).update_layout(width=120, height=110, margin={"t": 50, "b": 0, "l": 10, "r": 10})


def simple_indicator(
    value: float,
    title: str,
    _: str | None = None,
) -> go.Figure:
    """
    Create a simple indicator plot.

    Args:
    ----
        value (float): Current value.
        title (str): Title of the indicator.
        subtitle (str | None): Subtitle of the indicator.

    """
    title_text = f"""<span style='margin-bottom:2cm;font-size:1.2rem;font-weight:bold;'>{title}</span>""" # noqa: E501
    return go.Figure(
        go.Indicator(
            mode="number+delta",
            value=value,
            number={
                "prefix": "$",
                "font": {
                    "size": 40,
                },
            },
            title={
                "text": title_text,
            },
        )
    ).update_layout(width=180, height=110, margin={"t": 50, "b": 0, "l": 50, "r": 50})
