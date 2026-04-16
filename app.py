import streamlit as st
import requests
import re
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="SafeSchool | Secure Reporting", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS FOR PROFESSIONAL UI ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #004a99;
        color: white;
    }
    .login-card {
        padding: 2rem;
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .auth-header {
        text-align: center;
        color: #1e293b;
        font-family: 'Inter', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- AUTHENTICATION LOGIC ---
def login_counselor(username, password):
    # For Hackathon: Use simple check or st.secrets for credentials
    if username == "admin" and password == "counselor123":
        st.session_state.authenticated = True
        st.session_state.user_role = "Counselor"
        st.rerun()
    else:
        st.error("Invalid credentials")

def enter_as_student():
    st.session_state.authenticated = True
    st.session_state.user_role = "Student"
    st.rerun()

def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- UI COMPONENTS ---

# 1. LOGIN PAGE
if not st.session_state.authenticated:
    st.markdown("<h1 class='auth-header'>🛡️ SafeSchool Response Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Select your portal to continue</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.subheader("Student Portal")
        st.write("Submit a report 100% anonymously. No login required.")
        if st.button("Enter Anonymous Portal"):
            enter_as_student()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.subheader("Counselor Portal")
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Secure Login"):
            login_counselor(user, pw)
        st.markdown("</div>", unsafe_allow_html=True)

# 2. APP CONTENT
else:
    # Top Navigation Bar
    nav_col1, nav_col2 = st.columns([8, 1])
    nav_col1.title(f"🛡️ {st.session_state.user_role} Dashboard")
    if nav_col2.button("Logout"):
        logout()

    if st.session_state.user_role == "Student":
        # --- STUDENT REPORTING UI ---
        st.info("🔒 Your identity is hidden. The system automatically redacts personal info.")
        with st.form("incident_report"):
            report_text = st.text_area("What happened?")
            platform = st.selectbox("Platform", ["WhatsApp", "Instagram", "School App"])
            if st.form_submit_button("Submit Secure Report"):
                # Insert your Anonymize + API logic here
                st.success("Report submitted successfully.")

    elif st.session_state.user_role == "Counselor":
        # --- COUNSELOR DASHBOARD UI ---
        st.subheader("Recent Incidents")
        # Mock Data for UI Presentation
        data = pd.DataFrame({
            "ID": [101, 102],
            "Type": ["Verbal Abuse", "Threat"],
            "Severity": ["MEDIUM", "HIGH"],
            "Timestamp": ["2026-04-16 10:00", "2026-04-16 11:30"]
        })
        st.table(data)
        
        st.subheader("Analytics")
        st.bar_chart(data["Severity"].value_counts())
