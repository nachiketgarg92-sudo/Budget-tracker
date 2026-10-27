# Browse / search / delete transactions
from datetime import date

import pandas as pd
import streamlit as st
from auth import require_login
from db import run_query, run_action

user = require_login()
uid = user["user_id"]

st.title("Browse Transactions")

accounts = run_query("SELECT account_id, account_name FROM account WHERE user_id = %s", (uid,))
categories = run_query("SELECT category_id, category_name FROM category WHERE user_id = %s", (uid,))
tags = run_query("SELECT tag_id, tag_name FROM tag WHERE user_id = %s", (uid,))

# filters
dates = st.date_input("Date range", (date.today().replace(day=1), date.today()))
col1, col2, col3, col4 = st.columns(4)
f_type = col1.selectbox("Type", ["All", "Income", "Expense"])
f_cat = col2.selectbox("Category", ["All"] + [c["category_name"] for c in categories])
f_tag = col3.selectbox("Tag", ["All"] + [t["tag_name"] for t in tags])
f_acc = col4.selectbox("Account", ["All"] + [a["account_name"] for a in accounts])
search = st.text_input("Search merchant")

if len(dates) != 2:
    st.info("Select both a start and an end date")
    st.stop()

sql = (
    "SELECT t.transaction_id AS id, t.transaction_date AS date, t.transaction_type AS type, "
    "t.amount, c.category_name AS category, a.account_name AS account, g.tag_name AS tag, "
    "t.merchant_name AS merchant, t.notes "
    "FROM `transaction` t "
    "JOIN category c ON t.category_id = c.category_id "
    "JOIN account a ON t.account_id = a.account_id "
    "LEFT JOIN tag g ON t.tag_id = g.tag_id "
    "WHERE t.user_id = %s AND t.transaction_date BETWEEN %s AND %s"
)
params = [uid, dates[0], dates[1]]

if f_type != "All":
    sql += " AND t.transaction_type = %s"
    params.append(f_type)
if f_cat != "All":
    sql += " AND c.category_name = %s"
    params.append(f_cat)
if f_tag != "All":
    sql += " AND g.tag_name = %s"
    params.append(f_tag)
if f_acc != "All":
    sql += " AND a.account_name = %s"
    params.append(f_acc)
if search:
    sql += " AND t.merchant_name LIKE %s"
    params.append("%" + search + "%")
sql += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"

rows = run_query(sql, params)
if rows:
    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].astype(float)
    st.dataframe(df, hide_index=True)
    st.write("Rows:", len(df), "| Total amount:", df["amount"].sum())

    st.subheader("Delete a transaction")
    del_id = st.selectbox("Transaction id", df["id"].tolist())
    if st.button("Delete"):
        run_action("DELETE FROM `transaction` WHERE transaction_id = %s AND user_id = %s", (del_id, uid))
        st.rerun()
else:
    st.write("No transactions found.")
