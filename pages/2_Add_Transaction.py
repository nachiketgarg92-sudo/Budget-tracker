# Add a transaction
from datetime import date

import streamlit as st
from auth import require_login
from db import run_query, run_action

user = require_login()
uid = user["user_id"]

st.title("Add Transaction")

accounts = run_query("SELECT account_id, account_name FROM account WHERE user_id = %s", (uid,))
categories = run_query("SELECT category_id, category_name, category_type FROM category WHERE user_id = %s", (uid,))
tags = run_query("SELECT tag_id, tag_name FROM tag WHERE user_id = %s", (uid,))

if not accounts or not categories:
    st.warning("Please add at least one account and one category in the Manage page first.")
    st.stop()

acc_map = {a["account_name"]: a["account_id"] for a in accounts}
tag_map = {"(no tag)": None}
for t in tags:
    tag_map[t["tag_name"]] = t["tag_id"]

with st.form("add_txn"):
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    amount = st.number_input("Amount", min_value=0.0, step=10.0)
    t_date = st.date_input("Date", date.today())
    account = st.selectbox("Account", list(acc_map.keys()))
    cat_map = {c["category_name"]: c["category_id"] for c in categories}
    category = st.selectbox("Category", list(cat_map.keys()))
    tag = st.selectbox("Tag", list(tag_map.keys()))
    merchant = st.text_input("Merchant (optional)")
    notes = st.text_input("Notes (optional)")
    submit = st.form_submit_button("Save")

if submit:
    if amount <= 0:
        st.error("Amount must be greater than 0")
    else:
        run_action(
            "INSERT INTO `transaction` (user_id, account_id, category_id, tag_id, transaction_type, "
            "amount, transaction_date, merchant_name, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (uid, acc_map[account], cat_map[category], tag_map[tag], t_type, amount, t_date,
             merchant or None, notes or None),
        )
        st.success("Transaction saved!")
