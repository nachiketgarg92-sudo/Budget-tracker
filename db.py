# db.py - connects to MySQL and runs queries
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "budget_db"),
    )


def run_query(sql, params=None):
    """For SELECT. Returns a list of dictionaries."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def run_action(sql, params=None):
    """For INSERT / UPDATE / DELETE. Returns the new id (for inserts)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or ())
    conn.commit()
    new_id = cur.lastrowid
    cur.close()
    conn.close()
    return new_id
