#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
from db import load_table, save_table, seed_from_excel

st.set_page_config(page_title="Tipper Truck", layout="wide")
st.title("🚛 Tipper Truck Status & Whereabout")

# -------------------------
# Excel upload
# -------------------------
uploaded_file = st.file_uploader("Upload Tipper Truck Schedule (Excel)", type=["xlsx"])
if uploaded_file:
    seed_from_excel("tipper_schedule", uploaded_file)
    st.success("✅ Schedule uploaded successfully.")

# -------------------------
# Load data
# -------------------------
# df = load_table("tipper_schedule")

import db

df = db.load_table("tipper_schedule")


# -------------------------
# Current time
# -------------------------
from datetime import datetime
import pytz
sg_timezone = pytz.timezone("Asia/Singapore")
now_time = datetime.now(sg_timezone).time()
st.caption(f"🕒 Current Time (SG): {now_time.strftime('%H:%M')}")

# -------------------------
# Display status
# -------------------------
st.subheader("📅 Tipper Truck Schedule")
vehicle_filter = st.multiselect(
    "Filter by Vehicle",
    df["truck_id"].unique(),
    default=df["truck_id"].unique()
)
filtered_df = df[df["truck_id"].isin(vehicle_filter)]
st.dataframe(filtered_df.sort_values(["truck_id"]), use_container_width=True)

# -------------------------
# Whereabout update
# -------------------------
st.subheader("📍 Driver Whereabout Update (Auto-Save)")

with st.form("driver_update"):
    vehicle = st.selectbox("Vehicle", df["truck_id"].unique())
    location = st.text_input("Current Location / Site Code", placeholder="e.g. P201, P202, Depot")
    status = st.selectbox("Status", ["Available", "Busy"])
    remarks = st.text_input("Remarks")
    submit = st.form_submit_button("Update Whereabout")

if submit:
    mask = df["truck_id"] == vehicle
    if mask.any():
        df.loc[mask, "current_location"] = location
        df.loc[mask, "status"] = status
        df.loc[mask, "remarks"] = remarks
        df.loc[mask, "last_update"] = datetime.now(sg_timezone).strftime("%Y-%m-%d %H:%M")
        
#         save_table(df, "tipper_schedule")
        
        db.save_table(df, "tipper_schedule")
        
        st.success("✅ Whereabout updated and saved.")

