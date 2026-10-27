# Personal Budgeting, Expense Tracking & Tagging System

Stack: MySQL 8.0 + Python + Streamlit, with JWT login.

## Setup
1. Open `sql/schema.sql` in MySQL Workbench and run it (lightning button).
2. Copy `.env.example` to `.env` and fill in your MySQL password and a JWT secret.
   Make a secret with:  python -c "import secrets; print(secrets.token_hex(32))"
3. Install packages:   pip install -r requirements.txt
4. Run the app:        streamlit run app.py

## How JWT works here
- Register stores a bcrypt hash of the password (never the password itself).
- Login checks the hash, then creates a JWT (user_id, name, expiry 2 hours) signed with JWT_SECRET.
- The token is kept in st.session_state.
- Every page calls require_login(), which verifies the token's signature and expiry.
  The user_id comes only from the verified token, and every query filters by it,
  so one user can never see another user's data.
- Refreshing the browser tab clears the session, so you log in again.

## Files
- app.py            login / register
- auth.py           password hashing + JWT functions
- db.py             MySQL connection helpers
- pages/            Dashboard, Add Transaction, Browse, Budgets, Recurring, Manage
- sql/schema.sql    all tables
