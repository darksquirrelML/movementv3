#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import db  # your db.py for Supabase

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Pick-up Lorry Dashboard",
    page_icon="🚐",
    layout="wide"
)

st.title("🚐 Pick-up Lorry Dashboard")

# -------------------------
# MODULAR LOGIN SETTINGS
# -------------------------
ENABLE_LOGIN = True   # <-- Toggle True/False to enable login
USERNAME = "admin"    # <-- Set your username
PASSWORD = "1234"     # <-- Set your password

if ENABLE_LOGIN:
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("🔐 Login to upload schedule")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Invalid username or password")

# -------------------------
# LOAD CURRENT DATA
# -------------------------
df = db.load_table("pickup")

# -------------------------
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")
st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# 1️⃣ UPLOAD DAILY SCHEDULE (Excel)
# -------------------------
if not ENABLE_LOGIN or st.session_state.logged_in:
    st.subheader("📤 Upload Today's Schedule (Excel)")
    uploaded_file = st.file_uploader(
        "Select Excel file",
        type=["xlsx"],
        help="Columns must include: vehicle_id, plate_no, driver, time_start, time_end, current_location, status, remarks"
    )

    if uploaded_file is not None:
        try:
            new_df = pd.read_excel(uploaded_file)

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
                new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")
                db.save_table(new_df, "pickup")
                st.success("✅ Schedule uploaded and updated successfully!")
                df = db.load_table("pickup")  # reload

        except Exception as e:
            st.error(f"Failed to upload Excel: {e}")

# -------------------------
# 2️⃣ DRIVER WHEREABOUT UPDATE
# -------------------------
st.subheader("📍 Driver Whereabout Update")

vehicle = st.selectbox("Select Vehicle", df["vehicle_id"].unique())
vehicle_df = df[df["vehicle_id"] == vehicle].copy()

active_slot = vehicle_df[
    (vehicle_df["time_start"] <= now_str) & (vehicle_df["time_end"] >= now_str)
]

if active_slot.empty:
    upcoming = vehicle_df[vehicle_df["time_start"] > now_str].sort_values("time_start")
    target_slot = upcoming.iloc[[0]] if not upcoming.empty else vehicle_df.iloc[[0]]
else:
    target_slot = active_slot

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
    db.save_table(df, "pickup")
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
            ["vehicle_id", "plate_no", "driver", "current_location",
             "time_start", "time_end", "remarks", "last_updated"]
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

# Highlight active now
filtered_df["active_now"] = filtered_df.apply(
    lambda r: "✅ Active" if r["time_start"] <= now_str <= r["time_end"] else "",
    axis=1
)
st.dataframe(
    filtered_df.sort_values(["vehicle_id", "time_start"])[
        ["vehicle_id", "plate_no", "driver", "current_location",
         "status", "time_start", "time_end", "remarks", "last_updated", "active_now"]
    ],
    use_container_width=True
)

