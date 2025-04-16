import streamlit as st
from database import create_user_table, authenticate_user, init_dummy_users

def login_page():
    st.title("Login Sistem RAG")

    create_user_table()
    init_dummy_users()

    akun_preset = {
        "Admin (admin)": ("admin", "admin123"),
        "User (user01)": ("user01", "user01123")
    }

    akun_pilihan = st.selectbox("Pilih akun", list(akun_preset.keys()))
    username, password = akun_preset[akun_pilihan]

    st.text_input("Username", value=username, disabled=True)
    st.text_input("Password", value=password, disabled=True, type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user[0]
            st.experimental_set_query_params()
            st.success(f"Login berhasil sebagai {user[0]}")
            st.rerun()
        else:
            st.error("Username/password salah")
