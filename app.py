#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# import streamlit as st

# st.set_page_config(
#     page_title="Vehicle Movement Dashboard",
#     layout="wide"
# )

# st.title("🚚 Vehicle Movement Dashboard")

# st.markdown("""
# Please use the **sidebar** to navigate:
# - 🚐 Pick-up Lorry
# - 🚛 Tipper Truck
# - 🏗 Machinery
# """)


# In[ ]:


import streamlit as st

st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide"
)

st.title("🏠 Vehicle Movement Dashboard")

st.markdown("""
### Welcome

Use the menu on the left to navigate:

- 🚐 **Pickup Lorry**
- 🚚 **Tipper Truck**
- 🏗️ **Machinery**
""")

