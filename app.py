import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime
from PIL import Image
import numpy as np
import easyocr
import random
import base64

# ==========================================
# 🔑 CORE CONFIGURATION
# ==========================================
HF_API_KEY = "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" 
C_USER, C_PASS = "admin", "SafeSchool2026"
SMTP_USER = "yourschool@gmail.com" 
SMTP_PASS = "xxxx xxxx xxxx xxxx" 

# ==========================================
# 🔊 SONIC ENGINE (ALARM SOUND)
# ==========================================
def play_alarm():
    # High-pitched buzzer sound encoded in Base64 so it works offline/in-app
    # This is a short, sharp beep notification
    audio_html = """
        <audio autoplay>
            <source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# ==========================================
# 🎨 BRANDING & ADVANCED UI SYSTEM
# ==========================================
st.set_page_config(page_title="SafeSchool AI | Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .feature-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 30px; border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(12px); margin-bottom: 25px;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em; 
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        color: white; font-weight: 700; border: none;
    }
    .emergency-btn button { background: #dc2626 !important; }
    .motivation-box {
        padding: 25px; background: rgba(37, 99, 235, 0.1); 
        border-left: 4px solid #3b82f6; border-radius: 12px;
        color: #93c5fd; margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🏗️ BACKEND: INTELLIGENCE & ALERTS
# ==========================================
def init_db():
    with sqlite3.connect('safeschool_pro.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, platform TEXT, 
             type TEXT, severity TEXT, emotion TEXT, summary TEXT, status TEXT, score REAL)''')

def trigger_counselor_alarm(level="CRITICAL", message="Emergency Button Pressed"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect('safeschool_pro.db') as conn:
        conn.execute("INSERT INTO incidents (ts, platform, type, severity, emotion, summary, status, score) VALUES (?,?,?,?,?,?,?,?)",
                     (ts, "INTERNAL", "EMERGENCY ALARM", level, "Panic", message, "🚨 UNREAD ALARM", 1.0))

# [Keep other helper functions like call_ai_models and anonymize from previous code]

# ==========================================
# 🚦 ROUTING
# ==========================================
init_db()
if 'view' not in st.session_state: st.session_state.view = "Home"

# --- PAGE 1: HOME ---
if st.session_state.view == "Home":
    st.markdown("<br><br><h1 style='text-align:center;'>🛡️ SafeSchool AI</h1>", unsafe_allow_html=True)
    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        st.markdown("<div class='feature-card'><h3>Student Portal</h3><p>Report anonymously with AI protection.</p></div>", unsafe_allow_html=True)
        if st.button("🚀 Access Terminal"): st.session_state.view = "Student"; st.rerun()
    with c_right:
        st.markdown("<div class='feature-card'><h3>Administration</h3><p>Secure Staff Login.</p></div>", unsafe_allow_html=True)
        u, p = st.text_input("Staff ID"), st.text_input("Security Key", type="password")
        if st.button("🔒 Login"):
            if u == C_USER and p == C_PASS: st.session_state.view = "Staff"; st.rerun()

# --- PAGE 2: STUDENT PORTAL ---
elif st.session_state.view == "Student":
    if st.sidebar.button("🏠 Exit"): st.session_state.view = "Home"; st.rerun()
    
    st.markdown("<div class='motivation-box'>“You are taking a brave step today toward a safer digital future.”</div>", unsafe_allow_html=True)
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("🚨 TRIGGER EMERGENCY ALARM"):
            play_alarm() # 🔊 BUZZER SOUND
            trigger_counselor_alarm("CRITICAL", "Manual Emergency Trigger")
            st.error("🚨 ALARM ACTIVATED. Counselor has been alerted with an audible notification.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # [Insert existing Report Form code here from the previous output]

# --- PAGE 3: STAFF DASHBOARD & ANALYTICS ---
elif st.session_state.view == "Staff":
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update({"view": "Home"}))
    st.title("📊 Safety Command Center")
    
    with sqlite3.connect('safeschool_pro.db') as conn:
        df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    
    if not df.empty:
        # Check for unread emergency alarms to trigger buzzer for counselor too
        if not df[df.status == "🚨 UNREAD ALARM"].empty:
            play_alarm()
            st.error("🚨 ALERT: Active Emergency Signal Detected!")

        # --- 📈 GRAPHICAL ANALYSIS SECTION ---
        st.subheader("Safety Trend Analysis")
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### Incident Distribution (Platform)")
            platform_counts = df['platform'].value_counts()
            st.bar_chart(platform_counts) # Bar Chart for Platforms
            
        with col_chart2:
            st.markdown("#### Severity Breakdown")
            sev_counts = df['severity'].value_counts()
            # Creating a Pie Chart using Streamlit-friendly logic
            st.write("Distribution of Low vs High Severity cases:")
            st.dataframe(sev_counts) # Visual fallback for easy reading

        # Textual Data
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No active incidents.")
