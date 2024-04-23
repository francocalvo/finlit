"""
Create the monthly report for the given year and month.
"""

from decimal import Decimal
from logging import getLogger

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from beancount.query.query import run_query

from finlit.caching import Ledger

logger = getLogger()


@st.cache_data()
def get_expenses_for_month(_ledger: Ledger, year: int, month: int) -> pd.DataFrame:
    """
    Return a list of expenses for the given year and month.
    """

    query = f"""
        SELECT
          date,
          account,
          payee,
          narration,
          NUMBER(CONVERT(position, 'USD', date)) AS position
        WHERE account ~ '^Expenses'
        AND year(date) = {year}
        AND month(date) = {month}
        ORDER BY position DESC;
    """
    _, res = run_query(_ledger.entries, _ledger.options, query)

    return pd.DataFrame(res)


""" @st.cache_data() """


def get_total_expenses_for_month(_ledger: Ledger, year: int, month: int) -> float:
    """
    Return a list of expenses for the given year and month.
    """

    logger.info("Getting total expenses for month")

    query = f"""SELECT
          SUM(CONVERT(position, 'USD', date)) AS pos
        WHERE account ~ '^Expenses'
        AND year(date) = {year}
        AND month(date) = {month};
    """

    types, res = run_query(_ledger.entries, _ledger.options, query)

    return round(float(Decimal(res[0][0].get_positions()[0].sortkey()[3])), 2)


def html_expenses_card(total_expenses: float, daily: pd.DataFrame) -> str:
    """
    Return an HTML string for the expenses card.
    """

    # Convert the dataframe to a list of tuples
    daily_expenses_list = daily["position"].to_numpy().tolist()
    max_expense = max(daily_expenses_list)

    # Create the SVG line chart path dynamically
    """ svg_path_d = " ".join( """
    """     [ """
    """         f"M{10 + i * 20},{round((100 - float(expense)), 2)}" """
    """         for i, expense in enumerate(daily_expenses_list) """
    """     ] """
    """ ) """
    svg_path_d = "M" + " L".join(
        [
            f"{10 + i * 20},{100 - (expense / (max_expense) * 50)}"
            for i, expense in enumerate(daily_expenses_list)
        ]
    )

    print(svg_path_d)

    # Define the HTML content with dynamic data
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Streamlit Themed SVG with Overlay Text</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css">
    <style>
        :root {
            --streamlit-dark-bg: #1f2633; /* A dark background color */
            --streamlit-dark-text: #fafafa; /* A light text color for contrast */
            --streamlit-accent: #f63366; /* Streamlit's accent color */
            --streamlit-border: #2e2e2e; /* A border color for elements */
            --streamlit-shadow: rgba(0, 0, 0, 0.2); /* Shadow color for depth */
        }
        .chart-container {
            position: relative; /* Make this a positioning context */
            display: flex;
            flex-direction: column; /* Stack children vertically */
            justify-content: center;
            align-items: center;
            background-color: var(--streamlit-dark-bg);
            border-radius: 8px;
            color: var(--streamlit-dark-text);
            padding: 20px; /* Adjust padding to fit text */
            width: 350px; /* Smaller width */
            height: 250px; /* Fixed height to accommodate text */
            border: 1px solid var(--streamlit-border);
            box-shadow: 0 4px 8px var(--streamlit-shadow); /* Added shadow */
            margin: 20px; /* Space around the card */
        }
        .chart-text {
            position: absolute; /* Position text over SVG */
            width: 100%; /* Full width of the container */
            text-align: center; /* Center text horizontally */
            z-index: 10; /* Ensure text is above SVG */
        }
        .chart-title {
            top: 10px; /* Position at the top of the container */
        }
        .chart-value {
            bottom: 10px; /* Position at the bottom of the container */
        }
        svg {
            position: absolute; /* Position SVG to fill container */
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 5; /* Ensure SVG is below the text */
        }
    </style>
</head>
<body>
    <div class="chart-container streamlit-card">
        <div class="chart-text chart-title">Monthly Overview</div>
        <svg viewBox="0 0 400 200">
            <path fill="none" stroke="var(--streamlit-accent)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
            d="M10,150 L30,120 L50,130 L70,90 L90,80 L110,110 L130,70 L150,30 L170,95 L190,75 L210,85 L230,95 L250,100 L270,80 L290,85 L310,100 L330,95 L350,90"></path>
        </svg>
        <div class="chart-text chart-value">$249.43 USD</div>
    </div>
</body>
</html>
"""


def create_monthly_report(ledger: Ledger, year: int, month: int) -> None:
    """
    Create the monthly report for the given year and month.
    """

    logger.info("Creating the monthly report")

    st.subheader("Expenses for %s-%02d" % (year, month))

    expenses = get_expenses_for_month(ledger, year, month)
    expenses_per_day = expenses.groupby("date").agg({"position": "sum"})
    total_expenses = get_total_expenses_for_month(ledger, year, month)

    components.html(
        html_expenses_card(total_expenses, expenses_per_day), width=420, height=220
    )
    st.write(expenses_per_day)

    components.html(
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Streamlit Styled Card</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <link rel="stylesheet" href= "https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css">
            <style>
                :root {
                    --streamlit-dark-bg: #1f2633; /* A dark background color */
                    --streamlit-dark-text: #fafafa; /* A light text color for contrast */
                    --streamlit-accent: #f63366; /* Streamlit's accent color */
                    --streamlit-border: #2e2e2e; /* A border color for elements */
                }
                .streamlit-card {
                    background-color: var(--streamlit-dark-bg);
                    color: var(--streamlit-dark-text);
                    border-color: var(--streamlit-border);
                }
                .streamlit-card a {
                    color: var(--streamlit-accent);
                }
                .streamlit-card a:hover {
                    background-color: #242424; /* Slightly lighter than the card background for hover effect */
                }
            </style>
        </head>
        <body>
            <div class="max-w-sm mx-auto my-10">
                <div class="shadow-md border rounded-lg max-w-sm p-5 streamlit-card">
                    <svg viewBox="0 0 400 160">
                        <path fill="none" stroke="var(--streamlit-accent)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                        d="M10,150 L30,120 L50,130 L70,90 L90,80 L110,110 L130,70 L150,30 L170,95 L190,75 L210,85 L230,95 L250,100 L270,80 L290,85 L310,100 L330,95 L350,90"></path>
                    </svg>
                    <h5 class="font-bold text-2xl tracking-tight mb-2">Total Expenses</h5>
                    <p class="font-normal mb-3">$456.24 USD</p>
                </div>
            </div>
        </body>
        </html>
        """,
        height=280,
        width=400,
    )

    logger.info("Monthly report created")
    st.write(expenses)
