# Dashboard - totals, spend by category/tag, top merchants, budget vs actual
from datetime import date

import pandas as pd
import streamlit as st
from auth import require_login
from db import run_query

user = require_login()
uid = user["user_id"]

st.title("Dashboard")

today = date.today()
dates = st.date_input("Date range", (today.replace(day=1), today))
if len(dates) != 2:
    st.info("Select both a start and an end date")
    st.stop()
start, end = dates

# income / expense / net
rows = run_query(
    "SELECT transaction_type, SUM(amount) AS total FROM `transaction` "
    "WHERE user_id = %s AND transaction_date BETWEEN %s AND %s GROUP BY transaction_type",
    (uid, start, end),
)
totals = {r["transaction_type"]: float(r["total"]) for r in rows}
income = totals.get("Income", 0)
expense = totals.get("Expense", 0)

c1, c2, c3 = st.columns(3)
c1.metric("Income", income)
c2.metric("Expense", expense)
c3.metric("Net", income - expense)

# spend by category
st.subheader("Spend by category")
rows = run_query(
    "SELECT c.category_name, SUM(t.amount) AS total FROM `transaction` t "
    "JOIN category c ON t.category_id = c.category_id "
    "WHERE t.user_id = %s AND t.transaction_type = 'Expense' AND t.transaction_date BETWEEN %s AND %s "
    "GROUP BY c.category_name ORDER BY total DESC",
    (uid, start, end),
)
if rows:
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    st.bar_chart(df.set_index("category_name")["total"])
else:
    st.write("No expenses in this period.")

# spend by tag
st.subheader("Spend by tag")
rows = run_query(
    "SELECT g.tag_name, SUM(t.amount) AS total FROM `transaction` t "
    "JOIN tag g ON t.tag_id = g.tag_id "
    "WHERE t.user_id = %s AND t.transaction_type = 'Expense' AND t.transaction_date BETWEEN %s AND %s "
    "GROUP BY g.tag_name ORDER BY total DESC",
    (uid, start, end),
)
if rows:
    df = pd.DataFrame(rows)
    df["total"] = df["total"].astype(float)
    st.bar_chart(df.set_index("tag_name")["total"])
else:
    st.write("No tagged expenses in this period.")

# top merchants
st.subheader("Top merchants")
rows = run_query(
    "SELECT merchant_name, COUNT(*) AS times, SUM(amount) AS total FROM `transaction` "
    "WHERE user_id = %s AND transaction_type = 'Expense' AND merchant_name IS NOT NULL "
    "AND transaction_date BETWEEN %s AND %s "
    "GROUP BY merchant_name ORDER BY total DESC LIMIT 5",
    (uid, start, end),
)
if rows:
    st.dataframe(pd.DataFrame(rows))
else:
    st.write("No merchant data.")

# budget vs actual
st.subheader("Budget vs actual")
rows = run_query(
    "SELECT b.budget_name, b.limit_amount, COALESCE(SUM(t.amount), 0) AS spent "
    "FROM budget b "
    "LEFT JOIN budget_category bc ON b.budget_id = bc.budget_id "
    "LEFT JOIN `transaction` t ON t.category_id = bc.category_id AND t.user_id = b.user_id "
    "  AND t.transaction_type = 'Expense' AND t.transaction_date BETWEEN b.period_start AND b.period_end "
    "WHERE b.user_id = %s GROUP BY b.budget_id, b.budget_name, b.limit_amount",
    (uid,),
)
if rows:
    df = pd.DataFrame(rows)
    df["limit_amount"] = df["limit_amount"].astype(float)
    df["spent"] = df["spent"].astype(float)
    df["remaining"] = df["limit_amount"] - df["spent"]
    st.dataframe(df)
else:
    st.write("No budgets yet.")
