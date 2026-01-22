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



# =================================================
# CONFIGURATION
# =================================================
PAGE_TITLE = "🏗️ Machinery Dashboard"
TABLE_NAME = "machinery"   # change to: pickup / tipper / machinery




# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title=PAGE_TITLE",
    page_icon="🏗️",
    layout="wide"
)

st.title(PAGE_TITLE)

# -------------------------
# TIME (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")  # HH:MM

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# 1️⃣ UPLOAD DAILY SCHEDULE (Excel)
# -------------------------
st.subheader("📤 Upload Today's Machinery Schedule (Excel)")

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

        missing_cols = [c for c in required_cols if c not in new_df.columns]
        if missing_cols:
            st.error(f"Missing columns in Excel: {missing_cols}")
        else:
            # Add last_updated column
            new_df["last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

            # Save to Supabase
            save_table(new_df, "machinery")

            st.success("✅ Machinery schedule uploaded and saved successfully!")

    except Exception as e:
        st.error(f"Failed to upload Excel: {e}")

# -------------------------
# LOAD DATA
# -------------------------
try:
    df = load_table("machinery")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    df = pd.DataFrame(
        columns=[
            "machine_id", "machine_name", "operator",
            "current_location", "status", "remarks", "last_updated"
        ]
    )

if df.empty:
    st.warning("No machinery schedule found. Please upload the schedule first!")

# -------------------------
# 2️⃣ OPERATOR WHEREABOUT UPDATE
# -------------------------
if not df.empty:
    st.subheader("📍 Operator Whereabout Update")

    machine = st.selectbox("Select Machine", df["machine_id"].unique())

    machine_df = df[df["machine_id"] == machine].copy()

    target_slot = machine_df.iloc[[-1]]  # take latest row

    location_default = target_slot["current_location"].values[0]
    status_default = target_slot["status"].values[0]
    remarks_default = target_slot["remarks"].values[0]

    with st.form("operator_update"):
        location = st.text_input(
            "Current Location / Site Code",
            value=location_default,
            placeholder="e.g. P201, P202, On site"
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

        save_table(df, "machinery")
        st.success("✅ Whereabout updated successfully!")
        df = load_table("machinery")  # reload updated data

# -------------------------
# 3️⃣ AVAILABLE NOW
# -------------------------
if not df.empty:
    st.subheader("🟢 Available Now")

    available_now = df[df["status"] == "Available"]

    if available_now.empty:
        st.warning("No machinery is available now.")
    else:
        st.dataframe(
            available_now[
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

    filtered_df = df.copy()
    filtered_df["active_now"] = ""  # optional

    st.dataframe(
        filtered_df[
            ["machine_id", "machine_name", "operator",
             "current_location", "status", "remarks", "last_updated", "active_now"]
        ],
        use_container_width=True
    )

