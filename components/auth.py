import streamlit as st
import streamlit_authenticator as stauth
import re

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def render_auth(db):
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

    if st.session_state.user_id is None:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    if username and password:
                        user_id = db.verify_user(username, password)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.error("Please fill in all fields")

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Username")
                email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Register")
                
                if submitted:
                    if new_username and email and new_password and confirm_password:
                        if not is_valid_email(email):
                            st.error("Please enter a valid email address")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match")
                        else:
                            user_id = db.create_user(new_username, email, new_password)
                            if user_id:
                                st.success("Registration successful! Please login.")
                                st.session_state.user_id = user_id
                                st.rerun()
                            else:
                                st.error("Username or email already exists")
                    else:
                        st.error("Please fill in all fields")
        
        st.stop()
    else:
        if st.sidebar.button("Logout"):
            st.session_state.user_id = None
            st.rerun()

    return st.session_state.user_id
