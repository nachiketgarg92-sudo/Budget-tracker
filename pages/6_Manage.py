# Manage accounts, categories and tags
import pandas as pd
import streamlit as st
from auth import require_login
from db import run_query, run_action

user = require_login()
uid = user["user_id"]

st.title("Manage Accounts, Categories & Tags")

tab_acc, tab_cat, tab_tag = st.tabs(["Accounts", "Categories", "Tags"])

# ---------- accounts ----------
with tab_acc:
    with st.form("new_account"):
        a_name = st.text_input("Account name")
        a_type = st.selectbox("Type", ["Cash", "Bank", "Card"])
        a_bal = st.number_input("Opening balance", step=100.0)
        if st.form_submit_button("Add account"):
            if a_name:
                run_action(
                    "INSERT INTO account (user_id, account_name, account_type, opening_balance) VALUES (%s,%s,%s,%s)",
                    (uid, a_name, a_type, a_bal),
                )
                st.rerun()
            else:
                st.error("Enter a name")
    rows = run_query(
        "SELECT account_id AS id, account_name, account_type, opening_balance FROM account WHERE user_id = %s", (uid,)
    )
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)

# ---------- categories ----------
with tab_cat:
    cats = run_query("SELECT category_id, category_name FROM category WHERE user_id = %s", (uid,))
    parent_map = {"(none)": None}
    for c in cats:
        parent_map[c["category_name"]] = c["category_id"]

    with st.form("new_category"):
        c_name = st.text_input("Category name")
        c_type = st.selectbox("Type", ["Expense", "Income"])
        c_parent = st.selectbox("Parent category", list(parent_map.keys()))
        if st.form_submit_button("Add category"):
            if c_name:
                run_action(
                    "INSERT INTO category (user_id, parent_category_id, category_name, category_type) VALUES (%s,%s,%s,%s)",
                    (uid, parent_map[c_parent], c_name, c_type),
                )
                st.rerun()
            else:
                st.error("Enter a name")
    rows = run_query(
        "SELECT c.category_id AS id, c.category_name, c.category_type, p.category_name AS parent "
        "FROM category c LEFT JOIN category p ON c.parent_category_id = p.category_id "
        "WHERE c.user_id = %s",
        (uid,),
    )
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)

# ---------- tags ----------
with tab_tag:
    with st.form("new_tag"):
        tg_name = st.text_input("Tag name")
        if st.form_submit_button("Add tag"):
            if tg_name:
                try:
                    run_action("INSERT INTO tag (user_id, tag_name) VALUES (%s,%s)", (uid, tg_name))
                    st.rerun()
                except Exception:
                    st.error("You already have this tag")
            else:
                st.error("Enter a name")
    rows = run_query("SELECT tag_id AS id, tag_name FROM tag WHERE user_id = %s", (uid,))
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True)
