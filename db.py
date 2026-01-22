#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# -------------------------------------------------
# Database connection (Supabase)
# -------------------------------------------------
DATABASE_URL = st.secrets["SUPABASE_DB_URL"]

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

# -------------------------------------------------
# Initialise tables (safe to run every time)
# -------------------------------------------------
def init_db():
    with engine.begin() as conn:

        # Pick-up Lorry
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

        # Tipper Truck
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

        # Machinery
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
# Load table
# -------------------------------------------------
def load_table(table_name: str) -> pd.DataFrame:
    init_db()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

# -------------------------------------------------
# Save table (replace)
# -------------------------------------------------
def save_table(df: pd.DataFrame, table_name: str):
    df.to_sql(table_name, engine, if_exists="replace", index=False)

# -------------------------------------------------
# Connection test
# -------------------------------------------------
def test_connection():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


######### Below added for login ###########
        
def seed_from_excel(uploaded_file, table_name):
    df = pd.read_excel(uploaded_file)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
        
        

