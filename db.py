#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------------------------
# Database connection (Supabase Session Pooler)
# -------------------------------------------------
DATABASE_URL = st.secrets["SUPABASE_DB_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# -------------------------------------------------
# Initialise tables (safe to call always)
# -------------------------------------------------
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pickup (
                vehicle_id TEXT,
                plate_no TEXT,
                driver TEXT,
                time_start TEXT,
                time_end TEXT,
                current_location TEXT,
                status TEXT,
                remarks TEXT,
                last_updated TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tipper (
                truck_id TEXT,
                plate_no TEXT,
                driver TEXT,
                current_location TEXT,
                status TEXT,
                remarks TEXT,
                last_updated TEXT
            )
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS machinery (
                machine_id TEXT,
                machine_name TEXT,
                operator TEXT,
                current_location TEXT,
                status TEXT,
                remarks TEXT,
                last_updated TEXT
            )
        """))

# -------------------------------------------------
# Load table into DataFrame
# -------------------------------------------------
def load_table(table_name: str) -> pd.DataFrame:
    init_db()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

# -------------------------------------------------
# Replace table (ADMIN / Excel upload only)
# -------------------------------------------------
def replace_table(df: pd.DataFrame, table_name: str):
    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

# -------------------------------------------------
# Update table safely (normal operations)
# -------------------------------------------------
def save_table(df: pd.DataFrame, table_name: str):
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))
        df.to_sql(table_name, conn, if_exists="append", index=False)

# -------------------------------------------------
# Append rows (logs / GPS history)
# -------------------------------------------------
def append_table(df: pd.DataFrame, table_name: str):
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

# -------------------------------------------------
# Connection test
# -------------------------------------------------
def test_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

