# app.py - main page: login and register
import streamlit as st
from db import run_query, run_action
from auth import hash_password, check_password, create_token, verify_token

st.set_page_config(page_title="Budget Tracker")
st.title("Personal Budgeting, Expense Tracking & Tagging System")

token = st.session_state.get("token")
user = verify_token(token) if token else None

if user:
    st.success("Welcome, " + user["name"] + "!")
    st.write("Use the sidebar to open Dashboard, Add Transaction, Browse, Budgets, Recurring or Manage.")
    if st.button("Logout"):
        st.session_state.pop("token", None)
        st.rerun()
else:
    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            rows = run_query(
                "SELECT user_id, name, password_hash FROM user_account WHERE email = %s",
                (email,),
            )
            if rows and check_password(password, rows[0]["password_hash"]):
                st.session_state["token"] = create_token(rows[0]["user_id"], rows[0]["name"])
                st.rerun()
            else:
                st.error("Wrong email or password")

    with tab_register:
        name = st.text_input("Name")
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password (min 6 characters)", type="password", key="reg_pass")
        if st.button("Register"):
            if not name or not reg_email or len(reg_pass) < 6:
                st.error("Fill all fields (password at least 6 characters)")
            elif run_query("SELECT user_id FROM user_account WHERE email = %s", (reg_email,)):
                st.error("This email is already registered")
            else:
                uid = run_action(
                    "INSERT INTO user_account (name, email, password_hash) VALUES (%s, %s, %s)",
                    (name, reg_email, hash_password(reg_pass)),
                )
                # give the new user some starting data
                run_action(
                    "INSERT INTO account (user_id, account_name, account_type, opening_balance) VALUES (%s, 'Cash', 'Cash', 0)",
                    (uid,),
                )
                defaults = [("Salary", "Income"), ("Food", "Expense"), ("Transport", "Expense"),
                            ("Rent", "Expense"), ("Shopping", "Expense"),
                            ("Entertainment", "Expense"), ("Other", "Expense")]
                for cat_name, cat_type in defaults:
                    run_action(
                        "INSERT INTO category (user_id, category_name, category_type) VALUES (%s, %s, %s)",
                        (uid, cat_name, cat_type),
                    )
                st.success("Registered! Now go to the Login tab.")
