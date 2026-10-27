# Recurring templates
from datetime import date

import pandas as pd
import streamlit as st
from auth import require_login
from db import run_query, run_action

user = require_login()
uid = user["user_id"]

st.title("Recurring Transactions")

accounts = run_query("SELECT account_id, account_name FROM account WHERE user_id = %s", (uid,))
categories = run_query("SELECT category_id, category_name FROM category WHERE user_id = %s", (uid,))

if not accounts or not categories:
    st.warning("Add an account and a category first (Manage page).")
    st.stop()

acc_map = {a["account_name"]: a["account_id"] for a in accounts}
cat_map = {c["category_name"]: c["category_id"] for c in categories}

st.subheader("New template")
with st.form("new_template"):
    t_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
    amount = st.number_input("Amount", min_value=0.0, step=10.0)
    account = st.selectbox("Account", list(acc_map.keys()))
    category = st.selectbox("Category", list(cat_map.keys()))
    frequency = st.selectbox("Frequency", ["Weekly", "Monthly", "Yearly"])
    next_run = st.date_input("Next run date", date.today())
    notes = st.text_input("Notes (optional)")
    submit = st.form_submit_button("Save template")

if submit:
    if amount <= 0:
        st.error("Amount must be above 0")
    else:
        run_action(
            "INSERT INTO recurring_template (user_id, account_id, category_id, transaction_type, amount, "
            "frequency, next_run_date, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (uid, acc_map[account], cat_map[category], t_type, amount, frequency, next_run, notes or None),
        )
        st.success("Template saved!")

st.subheader("Your templates")
rows = run_query(
    "SELECT r.template_id AS id, r.transaction_type AS type, r.amount, c.category_name AS category, "
    "a.account_name AS account, r.frequency, r.next_run_date, r.notes "
    "FROM recurring_template r JOIN category c ON r.category_id = c.category_id "
    "JOIN account a ON r.account_id = a.account_id WHERE r.user_id = %s",
    (uid,),
)
if rows:
    df = pd.DataFrame(rows)
    df["amount"] = df["amount"].astype(float)
    st.dataframe(df, hide_index=True)

    del_id = st.selectbox("Template id to delete", df["id"].tolist())
    if st.button("Delete template"):
        try:
            run_action("DELETE FROM recurring_template WHERE template_id = %s AND user_id = %s", (del_id, uid))
            st.rerun()
        except Exception:
            st.error("This template already generated transactions, so it cannot be deleted.")
else:
    st.write("No templates yet.")

st.subheader("Generate due transactions")
st.write("Creates transactions for every template whose next run date is today or earlier.")
if st.button("Run due templates"):
    count = 0
    while count < 200:  # safety limit
        due = run_query(
            "SELECT * FROM recurring_template WHERE user_id = %s AND next_run_date <= CURDATE()", (uid,)
        )
        if not due:
            break
        for t in due:
            run_action(
                "INSERT INTO `transaction` (user_id, account_id, category_id, template_id, transaction_type, "
                "amount, transaction_date, notes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (uid, t["account_id"], t["category_id"], t["template_id"], t["transaction_type"],
                 t["amount"], t["next_run_date"], t["notes"]),
            )
            run_action(
                "UPDATE recurring_template SET next_run_date = CASE frequency "
                "WHEN 'Weekly' THEN DATE_ADD(next_run_date, INTERVAL 1 WEEK) "
                "WHEN 'Monthly' THEN DATE_ADD(next_run_date, INTERVAL 1 MONTH) "
                "ELSE DATE_ADD(next_run_date, INTERVAL 1 YEAR) END WHERE template_id = %s",
                (t["template_id"],),
            )
            count += 1
    st.success(str(count) + " transaction(s) created")
