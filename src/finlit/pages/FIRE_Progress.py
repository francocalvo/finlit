"""
Progress for Financial Independence Retire Early (FIRE) journey.
"""

from datetime import datetime
from logging import getLogger

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import pytz
import streamlit as st
from finlit.caching import Ledger, get_ledger
from finlit.utils import create_parser, setup_logger
from sqlalchemy import create_engine

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

IDEAL_EXPENSE_RATIO = 0.25
CRITICAL_EXPENSE_RATIO = 0.5


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

    year_list = list(range(2022, datetime.now(tz=tz).year + 1))[::-1]
    selected_year = st.selectbox("Select a year", year_list)

    if selected_year == datetime.now(tz=tz).year:
        # Only show months up to the current month
        month_list = list(range(1, datetime.now(tz=tz).month + 1))[::-1]
    else:
        month_list = list(range(1, 13))[::-1]

    selected_month = st.selectbox("Select a month", month_list)

    logger.info("Selected year: %s", selected_year)
    logger.info("Selected month: %s", selected_month)
    periodo = f"{selected_year}-{selected_month:02d}-01"

    logger.info("Selected period: %s", periodo)

st.title("Monthly Overview")

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


def make_gaughe_chart(expense_ratio: float, title: str) -> go.Figure:
    fig = go.Figure(layout=go.Layout(height=300, margin={"t": 0, "b": 0}))

    ideal_porcentage = IDEAL_EXPENSE_RATIO * 100
    critical_porcentage = CRITICAL_EXPENSE_RATIO * 100
    expense_porcentage = round(expense_ratio * 100, 2)

    bg_ideal_color = "#194226"
    bg_warning_color = "#423a19"
    bg_critical_color = "#42191c"

    fg_ideal_color = "#3fa660"
    fg_warning_color = "#a6933f"
    fg_critical_color = "#a63f47"

    bar_color: str
    if expense_ratio < IDEAL_EXPENSE_RATIO:
        bar_color = fg_ideal_color
    elif expense_ratio < CRITICAL_EXPENSE_RATIO:
        bar_color = fg_warning_color
    else:
        bar_color = fg_critical_color

    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=expense_porcentage,
            title={"text": title},
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
    fig.update_layout(plot_bgcolor="white")
    # Reduce margins and padding
    fig.update_layout(margin={"t": 0, "b": 0, "l": 0, "r": 0})

    return fig


def expenses_bar_chart(data: pd.DataFrame) -> alt.Chart:
    ex_usd = "expenses_usd"
    ex_ars = "expenses_ars"
    cat = "category"
    title = "Monthly Expenses per Category"

    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(ex_usd, title="USD"),
            y=alt.Y(
                cat,
                title="Category",
                sort="-x",
                axis=alt.Axis(labelLimit=200),
                scale=alt.Scale(paddingInner=0.1),
            ),
            tooltip=[
                alt.Tooltip(cat, title="Category"),
                alt.Tooltip(ex_usd, format="$.2f", title="In USD"),
                alt.Tooltip(ex_ars, format="$.2f", title="In ARS"),
            ],
        )
        .properties(title=title)
    )


def expenses_historic_line_chart(source: pd.DataFrame) -> alt.LayerChart:
    # Create a selection that chooses the nearest point & selects based on x-value
    columns = ["ratiobruto", "rationeto"]
    logger.info("Columns: %s", columns)
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
            color=alt.Color("category:N", title="Category", legend=None),
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
                alt.Tooltip("ratiobruto", type="quantitative", title="Gross Ratio"),
                alt.Tooltip("rationeto", type="quantitative", title="Net Ratio"),
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

all_expenses = pd.read_sql(
    f"""
SELECT
  Date AS Fecha,
  CONCAT(Category, ' ⟶ ', Subcategory) AS Categoria,
  Narration AS Descripcion,
  Amount_usd AS Cantidad
FROM fin.all_expenses
WHERE
  DATE_PART('YEAR', DATE) = DATE_PART('YEAR', TO_DATE('{periodo}', 'YYYY-MM-DD'))
  AND DATE_PART('MONTH', DATE) = DATE_PART('MONTH', TO_DATE('{periodo}', 'YYYY-MM-DD'))
ORDER BY date ASC
    """,
    engine,
)

net_expense_ratio = pd.read_sql(
    f"""
WITH IncomeSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Income
    FROM
        Fin.All_Income
    WHERE
        Origin = 'Job'
    GROUP BY
        Y,
        M
),
ExpenseSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Expenses
    FROM
        Fin.All_Expenses
    WHERE
        Subcategory != 'Comisiones'
    GROUP BY
        Y,
        M
)
SELECT
    E.Expenses / I.Income
FROM
    IncomeSum AS I
    LEFT JOIN ExpenseSum AS E ON I.Y = E.Y
        AND I.M = E.M
WHERE
    E.Y = DATE_PART('YEAR', TO_DATE('{periodo}', 'YYYY-MM-DD'))
    AND E.M = DATE_PART('MONTH', TO_DATE('{periodo}', 'YYYY-MM-DD'))
    """,
    engine,
).to_numpy()[0][0]

logger.info("Net expense ratio: %s", net_expense_ratio)

expenses_month = pd.read_sql(
    f"""
SELECT
  SUM(amount_ars) AS expenses_ars,
  SUM(amount_usd) AS expenses_usd
FROM
  fin.all_expenses
WHERE
  DATE_PART('YEAR', DATE) = DATE_PART('YEAR', TO_DATE('{periodo}', 'YYYY-MM-DD'))
  AND DATE_PART('MONTH', DATE) = DATE_PART('MONTH', TO_DATE('{periodo}', 'YYYY-MM-DD'))
    """,
    engine,
)

income_month = pd.read_sql(
    f"""
SELECT
    SUM(amount_ars) AS income_ars,
    SUM(amount_usd) AS income_usd
FROM
    fin.all_income
WHERE
    DATE_PART('YEAR', DATE) = DATE_PART('YEAR', TO_DATE('{periodo}', 'YYYY-MM-DD'))
    AND DATE_PART('MONTH', DATE) = DATE_PART('MONTH', TO_DATE('{periodo}', 'YYYY-MM-DD'))
        """,  # noqa: E501
    engine,
)


expenses_ars = expenses_month["expenses_ars"].to_numpy()[0]
expenses_usd = expenses_month["expenses_usd"].to_numpy()[0]
income_ars = income_month["income_ars"].to_numpy()[0]
income_usd = income_month["income_usd"].to_numpy()[0]

expenses_ars_str = format_number(expenses_ars, prefix="$")
expenses_usd_str = format_number(expenses_usd, posfix=" USD")
income_ars_str = format_number(income_ars, prefix="$")
income_usd_str = format_number(income_usd, posfix=" USD")

gross_expense_ratio = round(expenses_usd / income_usd, 2)

logger.info("Gross expense ratio: %s", gross_expense_ratio)

## Calculate left over and daily budget

left_over = income_ars * IDEAL_EXPENSE_RATIO - expenses_ars
left_over_str = format_number(left_over, prefix="$")

days_left = (
    datetime.now(tz=tz) - datetime.strptime(periodo, "%Y-%m-%d").astimezone(tz)
).days
daily_budget = left_over / days_left
daily_budget_str = format_number(daily_budget, prefix="$")


expenses_per_cat = pd.read_sql(
    f"""
WITH UniqueCategories AS (
    SELECT DISTINCT CATEGORY
    FROM Fin.All_Expenses
),
ExpensesForPeriod AS (
    SELECT
        CATEGORY,
        SUM(amount_usd) AS expenses_usd,
        SUM(amount_ars) AS expenses_ars
    FROM Fin.All_Expenses
    WHERE
        DATE_PART('YEAR', Date) = DATE_PART('YEAR', TO_DATE('{periodo}', 'YYYY-MM-DD'))
        AND DATE_PART('MONTH', Date) =
            DATE_PART('MONTH', TO_DATE('{periodo}', 'YYYY-MM-DD'))
    GROUP BY CATEGORY
)
SELECT
    uc.CATEGORY AS category,
    COALESCE(efp.expenses_usd, 0) AS expenses_usd,
    COALESCE(efp.expenses_ars, 0) AS expenses_ars
FROM UniqueCategories uc
LEFT JOIN ExpensesForPeriod efp
    ON uc.CATEGORY = efp.CATEGORY
ORDER BY expenses_usd DESC;
""",  # noqa: S608
    engine,
)

expenses_historic = pd.read_sql(
    """
WITH IncomeSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Income
    FROM
        Fin.All_Income
    GROUP BY
        Y,
        M
),
ExpenseSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Expenses
    FROM
        Fin.All_Expenses
    GROUP BY
        Y,
        M
),
NetIncomeSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Income
    FROM
        Fin.All_Income
    WHERE
        Origin = 'Job'
    GROUP BY
        Y,
        M
),
NetExpenseSum AS (
    SELECT
        DATE_PART('YEAR', DATE) AS Y,
        DATE_PART('MONTH', DATE) AS M,
        SUM(Amount_Usd) AS Expenses
    FROM
        Fin.All_Expenses
    WHERE
        Subcategory != 'Comisiones'
    GROUP BY
        Y,
        M
)
SELECT
    MAKE_DATE(CAST(E.Y AS int), CAST(E.M AS int), 2) AS x,
    ROUND(E.Expenses / I.Income * 100, 2) AS RatioBruto,
    ROUND(NE.Expenses / NI.Income * 100, 2) AS RatioNeto
FROM
    IncomeSum AS I
    LEFT JOIN ExpenseSum AS E ON I.Y = E.Y
        AND I.M = E.M
    LEFT JOIN NetIncomeSum AS NI ON I.Y = NI.Y
        AND I.M = NI.M
    LEFT JOIN NetExpenseSum AS NE ON I.Y = NE.Y
        AND I.M = NE.M
WHERE
    E.Y < DATE_PART('YEAR', CURRENT_DATE)
    OR (E.Y = DATE_PART('YEAR', CURRENT_DATE)
        AND E.M <= DATE_PART('MONTH', CURRENT_DATE))
ORDER BY
    X ASC
        """,
    engine,
)

expenses_historic = expenses_historic.set_index("x")
expenses_historic = expenses_historic.reset_index().melt(
    "x", var_name="category", value_name="y"
)

logger.info("Historic expenses: %s", expenses_historic)
logger.info("Columns: %s", expenses_historic.columns)


#######################
# Layout


cols = st.columns([1, 2], gap="large")

with cols[0]:
    st.subheader("Summary")
    subcols = st.columns(2)
    with subcols[0]:
        st.metric(label="Total Income (ARS)", value=income_ars_str)
        st.metric(label="Total Income (USD)", value=income_usd_str)
        st.metric(label="Ideal Left Over", value=left_over_str)

    with subcols[1]:
        st.metric(label="Total Expenses (ARS)", value=expenses_ars_str)
        st.metric(label="Total Expenses (USD)", value=expenses_usd_str)
        st.metric(label="Ideal Daily Budget", value=daily_budget_str)

    st.plotly_chart(
        make_gaughe_chart(
            net_expense_ratio,
            "Net Expense Ratio",
        ),
        use_container_width=True,
        theme=None,
    )

    st.plotly_chart(
        make_gaughe_chart(gross_expense_ratio, "Gross Expense Ratio"),
        use_container_width=True,
        theme=None,
    )


with cols[1]:
    chart = expenses_bar_chart(expenses_per_cat)
    st.altair_chart(chart, use_container_width=True)

    st.altair_chart(
        expenses_historic_line_chart(expenses_historic),  # type: ignore # noqa: PGH003
        use_container_width=True,
    )

    st.subheader("All Expenses")
    st.dataframe(
        all_expenses,
        use_container_width=True,
        hide_index=True,
        column_order=["fecha", "categoria", "cantidad", "descripcion"],
    )
