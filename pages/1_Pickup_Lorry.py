#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import db  # your db.py with Supabase connection

# -------------------------
# MODULAR LOGIN SETTINGS
# -------------------------
ENABLE_LOGIN = True       # <-- Toggle True/False to enable login
USERNAME = "admin"        # <-- Set your username
PASSWORD = "1234"         # <-- Set your password

def login_required():
    """Returns True if user successfully logged in"""
    if not ENABLE_LOGIN:
        return True

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        return True

    st.subheader("🔐 Login to upload schedule")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    login_clicked = st.button("Login")
    
    if login_clicked:
        if username_input == USERNAME and password_input == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Logged in successfully!")
            st.rerun()  # <-- immediately rerun to show upload section
        else:
            st.error("❌ Invalid username or password")

    return st.session_state.logged_in

# =================================================
# CONFIGURATION
# =================================================
PAGE_TITLE = "🚚 Pickup Lorry Schedule"
TABLE_NAME = "pickup"   # change to: pickup / tipper / machinery

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon="🚚",
    layout="wide"
)
st.title(PAGE_TITLE)

# -------------------------
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")  # HH:MM string
st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# 1️⃣ UPLOAD DAILY SCHEDULE (Excel)
# -------------------------
if login_required():  # <-- Only allow upload if logged in
    st.subheader("📤 Upload Today's Schedule (Excel)")

    uploaded_file = st.file_uploader(
        "Select Excel file",
        type=["xlsx"],
        help="Columns must include: vehicle_id, plate_no, driver, time_start, time_end, current_location, status, remarks"
    )

    if uploaded_file is not None:
        try:
            new_df = pd.read_excel(uploaded_file)

            # Required columns
            required_cols = [
                "vehicle_id", "plate_no", "driver",
                "time_start", "time_end",
                "current_location", "status",
                "remarks"
            ]
            missing_cols = [c for c in required_cols if c not in new_df.columns]
            if missing_cols:
                st.error(f"Missing columns in Excel: {missing_cols}")
            else:
                # Normalize times
                new_df["time_start"] = new_df["time_start"].astype(str).str.slice(0,5)
                new_df["time_end"] = new_df["time_end"].astype(str).str.slice(0,5)
                new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

                # Save to DB
                db.save_table(new_df, TABLE_NAME)
                st.success("✅ Schedule uploaded and updated successfully!")

        except Exception as e:
            st.error(f"Failed to upload Excel: {e}")

# -------------------------
# LOAD CURRENT DATA
# -------------------------
df = db.load_table(TABLE_NAME)

# Normalize times in case of previous inconsistencies
df["time_start"] = df["time_start"].astype(str).str.slice(0,5)
df["time_end"] = df["time_end"].astype(str).str.slice(0,5)

# -------------------------
# 2️⃣ DRIVER WHEREABOUT UPDATE
# -------------------------
st.subheader("📍 Driver Whereabout Update")

if df.empty:
    st.warning("No schedule data available. Please upload first.")
else:
    vehicle = st.selectbox("Select Vehicle", df["vehicle_id"].unique())
    vehicle_df = df[df["vehicle_id"] == vehicle].copy()

    # Find active slot or next
    active_slot = vehicle_df[
        (vehicle_df["time_start"] <= now_str) &
        (vehicle_df["time_end"] >= now_str)
    ]
    if active_slot.empty:
        upcoming = vehicle_df[vehicle_df["time_start"] > now_str].sort_values("time_start")
        target_slot = upcoming.iloc[[0]] if not upcoming.empty else vehicle_df.iloc[[0]]
    else:
        target_slot = active_slot

    # Pre-fill form
    location_default = target_slot["current_location"].values[0]
    status_default = target_slot["status"].values[0]
    remarks_default = target_slot["remarks"].values[0]

    with st.form("driver_update"):
        location = st.text_input(
            "Current Location / Site Code",
            value=location_default,
            placeholder="e.g. P201, P202, Dormitory, On road"
        )

        status = st.selectbox(
            "Status",
            ["Available", "Busy"],
            index=0 if status_default == "Available" else 1
        )

        remarks = st.text_input("Remarks", value=remarks_default)

        submit = st.form_submit_button("Update Whereabout")

    if submit:
        idx = target_slot.index
        df.loc[idx, "current_location"] = location
        df.loc[idx, "status"] = status
        df.loc[idx, "remarks"] = remarks
        df.loc[idx, "last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

        db.save_table(df, TABLE_NAME)
        df = db.load_table(TABLE_NAME)  # reload updated data
        st.success("✅ Whereabout updated successfully!")

# -------------------------
# 3️⃣ AVAILABLE NOW
# -------------------------
st.subheader("🟢 Available Now")
available_now = df[
    (df["status"] == "Available") &
    (df["time_start"] <= now_str) &
    (df["time_end"] >= now_str)
]
if available_now.empty:
    st.warning("No pick-up lorry available now.")
else:
    st.dataframe(
        available_now[
            ["vehicle_id", "plate_no", "driver",
             "current_location", "time_start", "time_end",
             "remarks", "last_updated"]
        ],
        use_container_width=True
    )

# -------------------------
# 4️⃣ TODAY'S SCHEDULE
# -------------------------
st.subheader("📅 Today's Pick-up Lorry Schedule")
vehicle_filter = st.multiselect(
    "Filter by Vehicle",
    df["vehicle_id"].unique(),
    default=df["vehicle_id"].unique()
)
filtered_df = df[df["vehicle_id"].isin(vehicle_filter)].copy()
if not filtered_df.empty:
    filtered_df["active_now"] = filtered_df.apply(
        lambda r: "✅ Active" if r["time_start"] <= now_str <= r["time_end"] else "",
        axis=1
    )
    st.dataframe(
        filtered_df.sort_values(["vehicle_id", "time_start"])[
            ["vehicle_id", "plate_no", "driver",
             "current_location", "status",
             "time_start", "time_end",
             "remarks", "last_updated", "active_now"]
        ],
        use_container_width=True
    )
else:
    st.warning("No schedule data available. Please upload first.")

