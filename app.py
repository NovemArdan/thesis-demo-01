import streamlit as st
from login import login_page
from dashboard import dashboard_main

# Inisialisasi session_state jika belum ada
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Login terlebih dahulu
if not st.session_state.logged_in:
    login_page()
else:
    dashboard_main()
