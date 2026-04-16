import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
from datetime import datetime
from PIL import Image
import numpy as np
import easyocr

# ==========================================
# 🎨 ULTIMATE UI STYLING (DARK & LIGHT COMPATIBLE)
# ==========================================
st.set_page_config(page_title="SafeSchool AI | Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    /* Force a professional dark-themed background for the whole app */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }

    /* Elegant Card Design - Fixed for visibility */
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 35px;
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid #3b82f6;
    }

    /* Text Colors - Forced for visibility */
    h1, h2, h3, p {
        color: #ffffff !important;
    }
    .sub-text {
        color: #94a3b8 !important;
        text-align: center;
        font-size: 18px;
    }

    /* Input Fields Styling */
    .stTextInput input {
        background-color: #1e293b !important;
        color: white !important;
        border: 1px solid #334155 !important;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white !important;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-weight: 700;
        width: 100%;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: #94a3b8 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #3b82f6 !important;
        border-bottom-color: #3b82f6 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- BACKEND FUNCTIONS (Keep your existing init_db, query_ai, etc. here) ---
# [Insert your existing logic functions here]

# --- PAGE ROUTING ---
if 'view' not in st.session_state: st.session_state.view = "Home"

if st.session_state.view == "Home":
    # Hero Section
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_title = st.columns([1, 10])
    with col_logo:
        st.image("https://cdn-icons-png.flaticon.com/512/3655/3655610.png", width=80)
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>SafeSchool AI</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-text' style='text-align:left;'>The Next-Gen Incident Response Platform</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2, gap="large")
    
    with col_left:
        st.markdown("""
            <div class='feature-card'>
                <h2>Student Portal</h2>
                <p>Submit reports with 100% anonymity. Our AI automatically scrubs your name and contact details to protect your identity.</p>
                <ul style='color:#94a3b8; margin-bottom:25px;'>
                    <li>Encrypted Data Transmission</li>
                    <li>Automated PII Redaction</li>
                    <li>Instant Support Routing</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start Anonymous Report"):
            st.session_state.view = "Student"; st.rerun()
            
    with col_right:
        st.markdown("<div class='feature-card'><h2>Staff Portal</h2><p>Access the administrative dashboard to manage cases and analyze safety trends.</p>", unsafe_allow_html=True)
        u_in = st.text_input("Administrator ID", placeholder="e.g. admin")
        p_in = st.text_input("Security Key", type="password", placeholder="••••••••")
        if st.button("🔒 Secure Login"):
            # Replace C_USER/C_PASS with your actual variables
            if u_in == "admin" and p_in == "SafeSchool2026":
                st.session_state.view = "Staff"; st.rerun()
            else:
                st.error("Authentication Failed")
        st.markdown("</div>", unsafe_allow_html=True)
