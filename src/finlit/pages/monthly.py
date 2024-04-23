"""
Create the monthly report for the given year and month.
"""

from logging import getLogger

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

logger = getLogger()

engine = create_engine("postgresql://postgres:postgres@localhost:5432/finances")

query = """
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
    MAKE_DATE(CAST(E.Y AS int), CAST(E.M AS int), 1) AS Date,
    E.Expenses / I.Income * 100 AS RatioBruto,
    NE.Expenses / NI.Income * 100 AS RatioNeto
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
    DATE ASC
"""

expenses_df = pd.read_sql(query, engine)

st.title("Monthly Report")
st.write("This is the monthly report for the given year and month.")
st.dataframe(expenses_df)
