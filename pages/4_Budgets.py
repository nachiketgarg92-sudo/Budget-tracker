# Budget manager
from datetime import date

import streamlit as st
from auth import require_login
from db import run_query, run_action

user = require_login()
uid = user["user_id"]

st.title("Budgets")

categories = run_query(
    "SELECT category_id, category_name FROM category WHERE user_id = %s AND category_type = 'Expense'", (uid,)
)
cat_map = {c["category_name"]: c["category_id"] for c in categories}

st.subheader("Create a budget")
with st.form("new_budget"):
    name = st.text_input("Budget name")
    limit = st.number_input("Limit amount", min_value=0.0, step=100.0)
    start = st.date_input("Start date", date.today().replace(day=1))
    end = st.date_input("End date", date.today())
    chosen = st.multiselect("Categories covered", list(cat_map.keys()))
    submit = st.form_submit_button("Create")

if submit:
    if not name or limit <= 0 or not chosen:
        st.error("Enter a name, a limit above 0, and at least one category")
    elif end < start:
        st.error("End date must be after start date")
    else:
        bid = run_action(
            "INSERT INTO budget (user_id, budget_name, limit_amount, period_start, period_end) VALUES (%s,%s,%s,%s,%s)",
            (uid, name, limit, start, end),
        )
        for c in chosen:
            run_action("INSERT INTO budget_category (budget_id, category_id) VALUES (%s, %s)", (bid, cat_map[c]))
        st.success("Budget created!")

st.subheader("Your budgets")
budgets = run_query(
    "SELECT b.budget_id, b.budget_name, b.limit_amount, b.period_start, b.period_end, "
    "COALESCE(SUM(t.amount), 0) AS spent "
    "FROM budget b "
    "LEFT JOIN budget_category bc ON b.budget_id = bc.budget_id "
    "LEFT JOIN `transaction` t ON t.category_id = bc.category_id AND t.user_id = b.user_id "
    "  AND t.transaction_type = 'Expense' AND t.transaction_date BETWEEN b.period_start AND b.period_end "
    "WHERE b.user_id = %s "
    "GROUP BY b.budget_id, b.budget_name, b.limit_amount, b.period_start, b.period_end "
    "ORDER BY b.period_end DESC",
    (uid,),
)

if not budgets:
    st.write("No budgets yet.")

for b in budgets:
    limit_amt = float(b["limit_amount"])
    spent = float(b["spent"])
    st.markdown("**" + b["budget_name"] + "**  (" + str(b["period_start"]) + " to " + str(b["period_end"]) + ")")
    st.progress(min(spent / limit_amt, 1.0))
    st.write("Spent", spent, "of", limit_amt, "| Remaining:", limit_amt - spent)
    if spent > limit_amt:
        st.error("Budget exceeded!")
    if st.button("Delete this budget", key="del_" + str(b["budget_id"])):
        run_action("DELETE FROM budget WHERE budget_id = %s AND user_id = %s", (b["budget_id"], uid))
        st.rerun()
    st.divider()
