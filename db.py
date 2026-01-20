#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# db.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# -------------------------
# Get SQLAlchemy engine from Supabase URL
# -------------------------
@st.cache_resource
def get_engine():
    engine = create_engine(st.secrets["SUPABASE_DB_URL"])
    return engine

engine = get_engine()

# -------------------------
# Table names
# -------------------------
TABLES = {
    "pickup": "pickup_schedule",
    "tipper": "tipper_schedule",
    "machinery": "machinery_schedule"
}

# -------------------------
# Load table into DataFrame
# -------------------------
def load_table(table_type: str) -> pd.DataFrame:
    """
    Load a table (pickup/tipper/machinery) from Supabase
    """
    table_name = TABLES[table_type]
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(query, engine)
    return df

# -------------------------
# Save DataFrame back to Supabase
# -------------------------
def save_table(df: pd.DataFrame, table_type: str):
    """
    Save a DataFrame back to Supabase
    """
    table_name = TABLES[table_type]
    df.to_sql(table_name, engine, if_exists="replace", index=False)

# -------------------------
# Initialize table from Excel (one-time use)
# -------------------------
def seed_from_excel(table_type: str, excel_file: str):
    """
    Upload an initial schedule from Excel
    """
    df = pd.read_excel(excel_file)
    save_table(df, table_type)

