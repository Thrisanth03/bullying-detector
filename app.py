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

# ==========================================
# 🔑 CORE CONFIGURATION
# ==========================================
# If using Streamlit Secrets (Recommended for security):
# HF_API_KEY = st.secrets["HF_API_KEY"]
HF_API_KEY = "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" 
C_USER, C_PASS = "admin", "SafeSchool2026"

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
    div[data-testid="stVerticalBlock"] > div:nth-child(1) .emergency-btn button { background: #dc2626 !important; }
    .motivation-box {
        padding: 25px; background: rgba(37, 99, 235, 0.1); 
        border-left: 4px solid #3b82f6; border-radius: 12px;
        color: #93c5fd; margin-bottom: 30px; font-style: italic;
    }
    input, textarea { background-color: #1e293b !important; color: white !important; border-color: #334155 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🏗️ BACKEND: RESOURCE CACHING (PREVENTS ERRORS)
# ==========================================
@st.cache_resource
def init_db():
    with sqlite3.connect('safeschool_pro.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, platform TEXT, 
             type TEXT, severity TEXT, emotion TEXT, summary TEXT, status TEXT, score REAL)''')

@st.cache_resource
def load_ocr_engine():
    # Loading OCR globally once to save 500MB+ of RAM
    return easyocr.Reader(['en'], gpu=False)

def play_alarm():
    audio_html = """<audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3" type="audio/mpeg"></audio>"""
    st.markdown(audio_html, unsafe_allow_html=True)

def trigger_counselor_alarm(level="CRITICAL", message="Immediate Help Requested"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect('safeschool_pro.db') as conn:
            conn.execute("INSERT INTO incidents (ts, platform, type, severity, emotion, summary, status, score) VALUES (?,?,?,?,?,?,?,?)",
                         (ts, "INTERNAL", "IMMEDIATE HELP", level, "Panic", message, "🚨 UNREAD ALARM", 1.0))
    except: pass

def call_ai_models(text):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    tox_api = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    emo_api = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
    try:
        t_res = requests.post(tox_api, headers=headers, json={"inputs": text}, timeout=10).json()
        e_res = requests.post(emo_api, headers=headers, json={"inputs": text}, timeout=10).json()
        return t_res[0][0]['score'], e_res[0][0]['label']
    except: return 0.4, "neutral"

def anonymize(text):
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    text = re.sub(r'\d{10}', '[PHONE]', text)
    return re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)

# ==========================================
# 🚦 MAIN ROUTING
# ==========================================
init_db()
reader = load_ocr_engine()

if 'view' not in st.session_state: st.session_state.view = "Home"

# --- PAGE 1: HOME ---
if st.session_state.view == "Home":
    st.markdown("<br><br><h1 style='text-align:center;'>🛡️ SafeSchool AI</h1>", unsafe_allow_html=True)
    c_left, c_right = st.columns(2, gap="large")
    with c_left:
        st.markdown("<div class='feature-card'><h3>Student Portal</h3><p>Secure incident reporting with real-time AI anonymization.</p></div>", unsafe_allow_html=True)
        if st.button("🚀 Access Terminal"): st.session_state.view = "Student"; st.rerun()
    with c_right:
        st.markdown("<div class='feature-card'><h3>Administration</h3><p>Command center for school counselors and staff.</p></div>", unsafe_allow_html=True)
        u, p = st.text_input("Staff ID"), st.text_input("Security Key", type="password")
        if st.button("🔒 Login"):
            if u == C_USER and p == C_PASS: st.session_state.view = "Staff"; st.rerun()
            else: st.error("Invalid Credentials")

# --- PAGE 2: STUDENT PORTAL ---
elif st.session_state.view == "Student":
    if st.sidebar.button("🏠 Exit"): st.session_state.view = "Home"; st.rerun()
    
    quotes = ["You are not alone. Reporting is the first step toward a safer school.", "Your voice matters.", "SafeSchool AI ensures your privacy is 100% protected."]
    st.markdown(f"<div class='motivation-box'>“{random.choice(quotes)}”</div>", unsafe_allow_html=True)
    
    # Incident Analysis Card
    st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
    st.markdown("### 📝 Incident Analysis Terminal")
    msg = st.text_area("Describe what happened or paste chat logs:")
    imgs = st.file_uploader("Upload Screenshots (Optional)", accept_multiple_files=True)
    
    c1, c2 = st.columns(2)
    plat = c1.selectbox("Platform", ["WhatsApp", "Instagram", "Discord", "Snapchat", "Other"])
    freq = c2.selectbox("Occurrence", ["First time", "Multiple times", "Persistent Bullying"])
    
    if st.button("Analyze & Secure Report"):
        with st.status("🛠️ Running AI Safeguard...", expanded=True) as s:
            ocr_text = ""
            if imgs:
                for img in imgs:
                    try:
                        res = reader.readtext(np.array(Image.open(img)))
                        ocr_text += " " + " ".join([r[1] for r in res])
                    except: st.warning("One image could not be processed.")
            
            clean = anonymize(msg + " " + ocr_text)
            tox, emo = call_ai_models(clean)
            
            if tox >= 0.80:
                trigger_counselor_alarm("HIGH TOXICITY", f"Critical alert detected via AI scanning.")
            
            with sqlite3.connect('safeschool_pro.db') as conn:
                conn.execute("INSERT INTO incidents (ts, platform, type, severity, emotion, summary, status, score) VALUES (?,?,?,?,?,?,?,?)",
                             (datetime.now().strftime("%Y-%m-%d %H:%M"), plat, "Cyberbullying", "HIGH" if tox > 0.7 else "LOW", emo, clean[:300], "Pending", tox))
            
            s.update(label="Report Secured!", state="complete")
            st.balloons(); st.success("Report submitted. Your identity remains anonymous.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Crisis Support Card
    st.subheader("🆘 Crisis Support")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("🚨 IMMEDIATE HELP"):
            play_alarm()
            trigger_counselor_alarm("CRITICAL", "Immediate Help Triggered by Student")
            st.error("🚨 ALARM SENT. A counselor has been alerted immediately.")
        st.markdown('</div>', unsafe_allow_html=True)
    with col_e2:
        if st.button("🤝 REQUEST COUNSELOR CALL"):
            trigger_counselor_alarm("HIGH", "Call Request")
            st.success("Request logged for priority follow-up.")

# --- PAGE 3: STAFF DASHBOARD ---
elif st.session_state.view == "Staff":
    st.sidebar.button("🚪 Logout", on_click=lambda: st.session_state.update({"view": "Home"}))
    st.title("📊 Safety Command Center")
    
    with sqlite3.connect('safeschool_pro.db') as conn:
        df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    
    if not df.empty:
        if not df[df.status == "🚨 UNREAD ALARM"].empty:
            play_alarm()
            st.error("⚠️ ACTIVE EMERGENCY ALARM DETECTED")

        # Visual Analytics
        c_ch1, c_ch2 = st.columns(2)
        with c_ch1:
            st.markdown("#### Incident Platforms")
            st.bar_chart(df['platform'].value_counts())
        with c_ch2:
            st.markdown("#### Severity Stats")
            st.write(df['severity'].value_counts())

        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No active reports.")
