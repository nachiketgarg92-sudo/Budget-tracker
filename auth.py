# auth.py - password hashing and JWT token functions
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret")
ALGORITHM = "HS256"
TOKEN_HOURS = 2


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password, password_hash):
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id, name):
    payload = {
        "user_id": user_id,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token):
    """Returns the payload if the token is valid, otherwise None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:  # expired, tampered, or invalid
        return None


def require_login():
    """Call this at the top of every page. Stops the page if not logged in."""
    token = st.session_state.get("token")
    user = verify_token(token) if token else None
    if user is None:
        st.session_state.pop("token", None)
        st.warning("Please log in first (go to the main page).")
        st.stop()
    st.sidebar.write("Logged in as: " + user["name"])
    if st.sidebar.button("Logout"):
        st.session_state.pop("token", None)
        st.rerun()
    return user
