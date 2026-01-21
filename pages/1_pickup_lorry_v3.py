#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
# coding: utf-8

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import db  # your db.py with load_table / save_table functions

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
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")  # HH:MM string

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# LOAD CURRENT DATA
# -------------------------
df = db.load_table("pickup")  # Load pickup lorry table

if df.empty:
    st.warning("No pickup lorry data found. Please upload schedule first.")
    st.stop()

# Normalize time columns (ensure strings)
df["time_start"] = df["time_start"].astype(str).str.slice(0,5)
df["time_end"] = df["time_end"].astype(str).str.slice(0,5)

# -------------------------
# 1️⃣ UPLOAD DAILY SCHEDULE (Excel)
# -------------------------
st.subheader("📤 Upload Today's Schedule (Excel)")

uploaded_file = st.file_uploader(
    "Select Excel file",
    type=["xlsx"],
    help="Columns must include: vehicle_id, plate_no, driver, time_start, time_end, current_location, status, remarks"
)

if uploaded_file is not None:
    try:
        # Read Excel
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
            # Normalize time columns
            new_df["time_start"] = new_df["time_start"].astype(str).str.slice(0,5)
            new_df["time_end"] = new_df["time_end"].astype(str).str.slice(0,5)

            # Add last_updated
            new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

            # Save to DB
            db.save_table(new_df, "pickup")

            st.success("✅ Schedule uploaded and updated successfully!")

            # Reload
            df = db.load_table("pickup")

    except Exception as e:
        st.error(f"Failed to upload Excel: {e}")

# -------------------------
# 2️⃣ DRIVER WHEREABOUT UPDATE
# -------------------------
st.subheader("📍 Driver Whereabout Update")

vehicle_ids = df["vehicle_id"].unique()
if len(vehicle_ids) == 0:
    st.warning("No vehicles found in database.")
    st.stop()

vehicle = st.selectbox("Select Vehicle", vehicle_ids)

vehicle_df = df[df["vehicle_id"] == vehicle].copy()

# Find active slot or next
active_slot = vehicle_df[
    (vehicle_df["time_start"] <= now_str) &
    (vehicle_df["time_end"] >= now_str)
]

if not active_slot.empty:
    target_slot = active_slot.iloc[[0]]
elif not vehicle_df.empty:
    target_slot = vehicle_df.iloc[[0]]
else:
    st.warning(f"No schedule found for vehicle {vehicle}.")
    st.stop()

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

    db.save_table(df, "pickup")  # Save updated data
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

# Highlight active now
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

