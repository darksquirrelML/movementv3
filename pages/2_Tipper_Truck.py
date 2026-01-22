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
ENABLE_LOGIN = True
USERNAME = "admin"
PASSWORD = "1234"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


def login_required_for_upload():
    if not ENABLE_LOGIN:
        return True

    if st.session_state.logged_in:
        return True

    st.subheader("🔐 Login to upload schedule")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Logged in successfully")
            st.rerun()  # <-- key fix (auto show upload)
        else:
            st.error("❌ Invalid username or password")

    return False


# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="🚛 Tipper Truck Dashboard",
    page_icon="🚛",
    layout="wide"
)

st.title("🚛 Tipper Truck Dashboard")

# =================================================
# TIME (Singapore)
# =================================================
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# =================================================
# 1️⃣ UPLOAD DAILY SCHEDULE (LOGIN REQUIRED)
# =================================================
st.subheader("📤 Upload Today's Schedule (Excel)")

if login_required_for_upload():
    uploaded_file = st.file_uploader(
        "Select Excel file",
        type=["xlsx"],
        help="Columns: truck_id, plate_no, driver, current_location, status, remarks"
    )

    if uploaded_file is not None:
        try:
            new_df = pd.read_excel(uploaded_file)

            required_cols = [
                "truck_id", "plate_no", "driver",
                "current_location", "status", "remarks"
            ]

            missing_cols = [c for c in required_cols if c not in new_df.columns]
            if missing_cols:
                st.error(f"Missing columns in Excel: {missing_cols}")
            else:
                new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")
                save_table(new_df, "tipper")
                st.success("✅ Schedule uploaded and saved successfully!")

        except Exception as e:
            st.error(f"Failed to upload Excel: {e}")

# =================================================
# LOAD DATA (PUBLIC – NO LOGIN)
# =================================================
try:
    df = load_table("tipper")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    df = pd.DataFrame(
        columns=[
            "truck_id", "plate_no", "driver",
            "current_location", "status", "remarks", "last_updated"
        ]
    )

if df.empty:
    st.warning("No tipper truck schedule found. Please upload the schedule first.")

# =================================================
# 2️⃣ DRIVER WHEREABOUT UPDATE (NO LOGIN)
# =================================================
if not df.empty:
    st.subheader("📍 Driver Whereabout Update")

    truck = st.selectbox("Select Truck", df["truck_id"].unique())

    truck_df = df[df["truck_id"] == truck].copy()
    target_row = truck_df.iloc[[-1]]

    with st.form("driver_update"):
        location = st.text_input(
            "Current Location / Site Code",
            value=target_row["current_location"].values[0]
        )

        status = st.selectbox(
            "Status",
            ["Available", "Busy"],
            index=0 if target_row["status"].values[0] == "Available" else 1
        )

        remarks = st.text_input(
            "Remarks",
            value=target_row["remarks"].values[0]
        )

        submit = st.form_submit_button("Update Whereabout")

    if submit:
        idx = target_row.index
        df.loc[idx, "current_location"] = location
        df.loc[idx, "status"] = status
        df.loc[idx, "remarks"] = remarks
        df.loc[idx, "last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

        save_table(df, "tipper")
        st.success("✅ Whereabout updated successfully!")
        st.rerun()

# =================================================
# 3️⃣ AVAILABLE NOW
# =================================================
if not df.empty:
    st.subheader("🟢 Available Now")

    available_now = df[df["status"] == "Available"]

    if available_now.empty:
        st.warning("No tipper truck is available now.")
    else:
        st.dataframe(
            available_now[
                ["truck_id", "plate_no", "driver",
                 "current_location", "status", "remarks", "last_updated"]
            ],
            use_container_width=True
        )

# =================================================
# 4️⃣ TODAY'S SCHEDULE
# =================================================
if not df.empty:
    st.subheader("📅 Today's Tipper Truck Schedule")

    df["active_now"] = ""

    st.dataframe(
        df[
            ["truck_id", "plate_no", "driver",
             "current_location", "status",
             "remarks", "last_updated", "active_now"]
        ],
        use_container_width=True
    )

