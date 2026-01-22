#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from db import load_table, save_table, seed_from_excel

# =================================================
# CONFIGURATION
# =================================================
PAGE_TITLE = "🚚 Pickup Lorry Schedule"
TABLE_NAME = "pickup"   # change to: pickup / tipper / machinery

ENABLE_LOGIN = True     # 🔁 toggle ON/OFF easily
USERNAME = "admin"
PASSWORD = "1234"

# =================================================
# PAGE SETUP
# =================================================
st.set_page_config(page_title=PAGE_TITLE, layout="wide")
st.title(PAGE_TITLE)

# =================================================
# GLOBAL LOGIN (WORKS ACROSS ALL PAGES)
# =================================================
if ENABLE_LOGIN:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    with st.sidebar:
        st.subheader("🔐 Upload Access")

        if not st.session_state.logged_in:
            st.caption("Login required for schedule upload only")
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")

            if st.button("Login"):
                if u == USERNAME and p == PASSWORD:
                    st.session_state.logged_in = True
                    st.success("Logged in successfully")
                else:
                    st.error("Invalid username or password")
        else:
            st.success("Upload enabled")
            if st.button("Logout"):
                st.session_state.logged_in = False

# =================================================
# LOAD DATA (NO LOGIN REQUIRED)
# =================================================
df = load_table(TABLE_NAME)

if df.empty:
    st.info("No data available yet.")
else:
    st.subheader("📋 Current Status")
    st.dataframe(df, use_container_width=True)

# =================================================
# UPLOAD SECTION (LOGIN-PROTECTED)
# =================================================
st.divider()
st.subheader("📤 Upload Schedule")

if not ENABLE_LOGIN or st.session_state.logged_in:
    uploaded_file = st.file_uploader(
        "Upload Excel schedule (.xlsx)",
        type=["xlsx"]
    )

    if uploaded_file:
        try:
            seed_from_excel(uploaded_file, TABLE_NAME)
            st.success("✅ Schedule uploaded successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Upload failed: {e}")
else:
    st.info("🔒 Login required to upload schedule")

# =================================================
# WHEREABOUT / STATUS UPDATE (OPTIONAL – NO LOGIN)
# =================================================
st.divider()
st.subheader("📍 Update Whereabouts")

if not df.empty:
    vehicle_list = df["vehicle_id"].dropna().unique()
    selected_vehicle = st.selectbox("Select Vehicle", vehicle_list)

    vehicle_df = df[df["vehicle_id"] == selected_vehicle]

    location = st.text_input(
        "Current Location",
        value=vehicle_df.iloc[0].get("current_location", "")
    )

    status = st.selectbox(
        "Status",
        ["Idle", "On Route", "Working", "Completed"],
        index=0
    )

    remarks = st.text_input(
        "Remarks",
        value=vehicle_df.iloc[0].get("remarks", "")
    )

    if st.button("Update Status"):
        df.loc[df["vehicle_id"] == selected_vehicle, "current_location"] = location
        df.loc[df["vehicle_id"] == selected_vehicle, "status"] = status
        df.loc[df["vehicle_id"] == selected_vehicle, "remarks"] = remarks
        df.loc[df["vehicle_id"] == selected_vehicle, "last_updated"] = pd.Timestamp.now()

        save_table(df, TABLE_NAME)
        st.success("Status updated")
        st.rerun()

