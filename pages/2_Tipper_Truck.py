#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from db import load_table, save_table

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="🚚 Tipper Truck Dashboard",
    page_icon="🚛",
    layout="wide"
)

st.title("🚛 Tipper Truck Dashboard")

# -------------------------
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")  # HH:MM

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# LOAD DATA
# -------------------------
try:
    df = load_table("tipper")  # match table name in db.py
except Exception as e:
    st.error(f"Failed to load data: {e}")
    df = pd.DataFrame(
        columns=[
            "truck_id", "plate_no", "driver",
            "current_location", "status", "remarks", "last_updated"
        ]
    )

if df.empty:
    st.warning("No tipper truck schedule found. Please upload the schedule first!")

# -------------------------
# DRIVER WHEREABOUT UPDATE
# -------------------------
if not df.empty:
    st.subheader("📍 Driver Whereabout Update")

    truck = st.selectbox("Select Truck", df["truck_id"].unique())

    truck_df = df[df["truck_id"] == truck].copy()

    # Take the latest row as the target
    target_slot = truck_df.iloc[[-1]]

    location_default = target_slot["current_location"].values[0]
    status_default = target_slot["status"].values[0]
    remarks_default = target_slot["remarks"].values[0]

    with st.form("driver_update"):
        location = st.text_input(
            "Current Location / Site Code",
            value=location_default,
            placeholder="e.g. P201, P202, On road"
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

        save_table(df, "tipper")
        st.success("✅ Whereabout updated successfully!")
        df = load_table("tipper")  # reload updated data

# -------------------------
# AVAILABLE NOW
# -------------------------
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

# -------------------------
# TODAY'S SCHEDULE
# -------------------------
if not df.empty:
    st.subheader("📅 Today's Tipper Truck Schedule")

    filtered_df = df.copy()

    if not filtered_df.empty:
        filtered_df["active_now"] = ""  # For tipper trucks, optional
        st.dataframe(
            filtered_df[
                ["truck_id", "plate_no", "driver",
                 "current_location", "status", "remarks", "last_updated", "active_now"]
            ],
            use_container_width=True
        )

