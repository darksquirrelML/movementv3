#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from db import load_table, save_table

# =================================================
# LOGIN CONFIG (UPLOAD ONLY)
# =================================================
ENABLE_LOGIN = True        # toggle ON/OFF easily
USERNAME = "admin"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_for_upload():
    if not ENABLE_LOGIN:
        return True

    if st.session_state.logged_in:
        return True

    st.subheader("🔐 Login to upload machinery schedule")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == USERNAME and p == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Logged in successfully")
            st.rerun()   # <-- IMPORTANT (fix double-click issue)
        else:
            st.error("❌ Invalid username or password")

    return False


# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="🏗️ Machinery Dashboard",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Machinery Dashboard")

# -------------------------
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# 1️⃣ UPLOAD DAILY SCHEDULE (LOGIN REQUIRED)
# -------------------------
st.subheader("📤 Upload Today's Machinery Schedule (Excel)")

if login_for_upload():

    uploaded_file = st.file_uploader(
        "Select Excel file",
        type=["xlsx"],
        help="Columns must include: machine_id, machine_name, operator, current_location, status, remarks"
    )

    if uploaded_file is not None:
        try:
            new_df = pd.read_excel(uploaded_file)

            required_cols = [
                "machine_id", "machine_name", "operator",
                "current_location", "status", "remarks"
            ]

            missing = [c for c in required_cols if c not in new_df.columns]
            if missing:
                st.error(f"Missing columns in Excel: {missing}")
            else:
                new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")
                save_table(new_df, "machinery")
                st.success("✅ Machinery schedule uploaded successfully!")

        except Exception as e:
            st.error(f"Failed to upload Excel: {e}")

# -------------------------
# LOAD DATA
# -------------------------
try:
    df = load_table("machinery")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    df = pd.DataFrame(columns=[
        "machine_id", "machine_name", "operator",
        "current_location", "status", "remarks", "last_updated"
    ])

if df.empty:
    st.warning("No machinery schedule found. Please upload the schedule first.")

# -------------------------
# 2️⃣ OPERATOR WHEREABOUT UPDATE (NO LOGIN)
# -------------------------
if not df.empty:
    st.subheader("📍 Operator Whereabout Update")

    machine = st.selectbox("Select Machine", df["machine_id"].unique())
    machine_df = df[df["machine_id"] == machine].copy()
    target = machine_df.iloc[[-1]]

    with st.form("operator_update"):
        location = st.text_input(
            "Current Location / Site Code",
            value=target["current_location"].values[0]
        )

        status = st.selectbox(
            "Status",
            ["Available", "Busy"],
            index=0 if target["status"].values[0] == "Available" else 1
        )

        remarks = st.text_input(
            "Remarks",
            value=target["remarks"].values[0]
        )

        submit = st.form_submit_button("Update Whereabout")

    if submit:
        idx = target.index
        df.loc[idx, ["current_location", "status", "remarks"]] = [
            location, status, remarks
        ]
        df.loc[idx, "last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")
        save_table(df, "machinery")
        st.success("✅ Whereabout updated successfully!")
        st.rerun()

# -------------------------
# 3️⃣ AVAILABLE NOW
# -------------------------
if not df.empty:
    st.subheader("🟢 Available Now")

    available = df[df["status"] == "Available"]

    if available.empty:
        st.warning("No machinery is available now.")
    else:
        st.dataframe(
            available[
                ["machine_id", "machine_name", "operator",
                 "current_location", "status", "remarks", "last_updated"]
            ],
            use_container_width=True
        )

# -------------------------
# 4️⃣ TODAY'S SCHEDULE
# -------------------------
if not df.empty:
    st.subheader("📅 Today's Machinery Schedule")

    df["active_now"] = ""
    st.dataframe(
        df[
            ["machine_id", "machine_name", "operator",
             "current_location", "status", "remarks",
             "last_updated", "active_now"]
        ],
        use_container_width=True
    )

