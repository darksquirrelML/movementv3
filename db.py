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
    pool_pre_ping=True
)

# -------------------------------------------------
# Initialise tables (run once, safe to call always)
# -------------------------------------------------
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS pickup (
                truck_id TEXT,
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
    query = f"SELECT * FROM {table_name}"
    return pd.read_sql(query, engine)

# -------------------------------------------------
# Save DataFrame back to table (replace mode)
# -------------------------------------------------
def save_table(df: pd.DataFrame, table_name: str):
    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

# -------------------------------------------------
# Append rows (optional, safer for logs)
# -------------------------------------------------
def append_table(df: pd.DataFrame, table_name: str):
    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False
    )

# -------------------------------------------------
# Simple connection test (optional)
# -------------------------------------------------
def test_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

