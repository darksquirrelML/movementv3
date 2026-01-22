#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import db

# =================================================
# LOGIN CONFIG (shared behaviour)
# =================================================
ENABLE_LOGIN = True
USERNAME = "admin"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_required():
    if not ENABLE_LOGIN or st.session_state.logged_in:
        return True

    st.subheader("🔐 Login to upload schedule")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == USERNAME and p == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Logged in successfully!")
            st.rerun()
        else:
            st.error("❌ Invalid login")

    return False

# =================================================
# CONFIGURATION
# =================================================
PAGE_TITLE = "🚛 Tipper Truck Schedule"
TABLE_NAME = "tipper"

st.set_page_config(page_title=PAGE_TITLE, page_icon="🚛", layout="wide")
st.title(PAGE_TITLE)

# =================================================
# TIME (SG)
# =================================================
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# =================================================
# UPLOAD (LOGIN REQUIRED)
# =================================================
if login_required():
    st.subheader("📤 Upload Tipper Truck Schedule")

    uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

    if uploaded_file:
        try:
            df_new = pd.read_excel(uploaded_file)

            required = [
                "vehicle_id", "plate_no", "driver",
                "time_start", "time_end",
                "current_location", "status", "remarks"
            ]

            missing = [c for c in required if c not in df_new.columns]
            if missing:
                st.error(f"Missing columns: {missing}")
            else:
                df_new["time_start"] = df_new["time_start"].astype(str).str[:5]
                df_new["time_end"] = df_new["time_end"].astype(str).str[:5]
                df_new["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

                db.save_table(df_new, TABLE_NAME)
                st.success("✅ Tipper schedule uploaded")

        except Exception as e:
            st.error(e)

# =================================================
# VIEW DATA (NO LOGIN REQUIRED)
# =================================================
df = db.load_table(TABLE_NAME)

if df.empty:
    st.warning("No data available.")
    st.stop()

df["time_start"] = df["time_start"].astype(str).str[:5]
df["time_end"] = df["time_end"].astype(str).str[:5]

# =================================================
# AVAILABLE NOW
# =================================================
st.subheader("🟢 Available Now")

available = df[
    (df["status"] == "Available") &
    (df["time_start"] <= now_str) &
    (df["time_end"] >= now_str)
]

st.dataframe(available, use_container_width=True)

# =================================================
# TODAY SCHEDULE
# =================================================
st.subheader("📅 Today's Tipper Schedule")
st.dataframe(df.sort_values(["vehicle_id", "time_start"]), use_container_width=True)

