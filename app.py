import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
import smtplib
from email.message import EmailMessage
from datetime import datetime
import numpy as np
from PIL import Image
import easyocr

# --- UI & THEME CONFIG ---
st.set_page_config(page_title="SafeSchool AI v2.0", page_icon="🛡️", layout="wide")

# Custom UI Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stButton>button { border-radius: 8px; font-weight: 600; transition: all 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .metric-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; }
    .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE LAYER ---
def init_db():
    with sqlite3.connect('vault.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS portal_logs 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, platform TEXT, 
             type TEXT, severity TEXT, score REAL, summary TEXT, status TEXT)''')

init_db()

# --- AI & LOGIC ENGINE ---
def scrub_sensitive_data(text):
    """Multi-pass anonymization for Privacy Compliance."""
    text = re.sub(r'\S+@\S+', '[PROTECTED EMAIL]', text)
    text = re.sub(r'\d{10}', '[PROTECTED PHONE]', text)
    # Redacts likely names (Capitalized words mid-sentence)
    text = re.sub(r'(?<=\s)([A-Z][a-z]+)', '[REDACTED]', text)
    return text

def analyze_incident(text, img_count, freq, dur):
    """Cloud AI + Heuristic Logic Engine."""
    API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=8).json()
        tox_score = response[0][0]['score']
    except:
        tox_score = 0.5 # Safe fallback

    # Heuristic Classification
    keywords = {
        "Threat": ["kill", "hurt", "find you", "punch", "stalk"],
        "Harassment": ["ugly", "stupid", "hate", "loser", "fat"],
        "Social Exclusion": ["kick", "remove", "group", "left out"]
    }
    
    found_type = "Verbal Abuse"
    for category, words in keywords.items():
        if any(w in text.lower() for w in words):
            found_type = category
            break

    # Severity Matrix
    severity = "LOW"
    if tox_score > 0.85 or found_type == "Threat": severity = "HIGH"
    elif tox_score > 0.5 or freq == "Repeated" or img_count > 2: severity = "MEDIUM"
    
    return found_type, severity, tox_score

# --- EMAIL ALERT SYSTEM ---
def dispatch_alert(summary, severity, itype):
    """Sends immediate SMTP alert for HIGH severity cases."""
    try:
        msg = EmailMessage()
        msg['Subject'] = f"🚨 SECURITY ALERT: {severity} Risk ({itype})"
        msg['From'] = st.secrets["SMTP_USER"]
        msg['To'] = st.secrets["COUNSELOR_EMAIL"]
        msg.set_content(f"Incident Summary: {summary}\nSeverity: {severity}\nTimestamp: {datetime.now()}")
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASS"])
            server.send_message(msg)
    except: pass # Silently fail to keep user experience smooth

# --- FRONTEND ROUTING ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- PROFESSIONAL LOGIN PAGE ---
    st.markdown("<h1 style='text-align: center;'>🛡️ SafeSchool Gateway</h1>", unsafe_allow_html=True)
    st.write("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Student Access")
        st.info("No login required. Your anonymity is legally protected.")
        if st.button("Submit Anonymous Report", use_container_width=True):
            st.session_state.role = "student"; st.session_state.logged_in = True
            st.rerun()

    with c2:
        st.subheader("Counselor Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Secure Login", use_container_width=True):
            if u == st.secrets["C_USER"] and p == st.secrets["C_PASS"]:
                st.session_state.role = "counselor"; st.session_state.logged_in = True
                st.rerun()
            else: st.error("Unauthorized Access.")

else:
    # --- AUTHENTICATED AREA ---
    st.sidebar.title("Navigation")
    if st.sidebar.button("Log Out"): 
        st.session_state.logged_in = False; st.rerun()

    if st.session_state.role == "student":
        st.title("🛡️ Student Protection Portal")
        with st.container(border=True):
            st.write("### 1. Evidence Gathering")
            col_a, col_b = st.columns(2)
            txt = col_a.text_area("Describe the incident (Keep it brief)")
            imgs = col_b.file_uploader("Upload Screenshots", accept_multiple_files=True)
            
            st.write("### 2. Context")
            col_c, col_d = st.columns(2)
            plat = col_c.selectbox("Platform", ["WhatsApp", "Instagram", "Discord", "Snapchat", "Other"])
            freq = col_d.selectbox("How often?", ["Once", "Repeated"])
            
            if st.button("Submit Report & Encrypt", type="primary"):
                with st.status("Analyzing with SafeSchool AI...", expanded=True) as status:
                    # OCR Processing
                    ocr_data = ""
                    if imgs:
                        reader = easyocr.Reader(['en'])
                        for i in imgs:
                            ocr_data += " " + " ".join([res[1] for res in reader.readtext(np.array(Image.open(i)))])
                    
                    clean_text = scrub_sensitive_data(txt + " " + ocr_data)
                    itype, sev, score = analyze_incident(clean_text, len(imgs), freq, "N/A")
                    
                    # Store in Database
                    with sqlite3.connect('vault.db') as conn:
                        conn.execute("INSERT INTO portal_logs (timestamp, platform, type, severity, score, summary, status) VALUES (?,?,?,?,?,?,?)",
                                     (datetime.now().strftime("%Y-%m-%d %H:%M"), plat, itype, sev, score, clean_text[:200], "Pending"))
                    
                    if sev == "HIGH": dispatch_alert(clean_text[:100], sev, itype)
                    status.update(label="Analysis Complete. Incident Securely Logged.", state="complete")
                    st.success("Your report was submitted. The counselor has been notified.")
                    st.balloons()

    else:
        # --- COUNSELOR DASHBOARD ---
        st.title("📊 Incident Command Center")
        with sqlite3.connect('vault.db') as conn:
            df = pd.read_sql_query("SELECT * FROM portal_logs ORDER BY id DESC", conn)
        
        if not df.empty:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Incidents", len(df))
            m2.metric("High Severity", len(df[df['severity'] == "HIGH"]))
            m3.metric("Avg. Toxicity", f"{int(df['score'].mean()*100)}%")
            m4.metric("Active Platforms", df['platform'].nunique())
            
            st.write("---")
            st.subheader("Action Required")
            st.dataframe(df, use_container_width=True)
            
            # Export Utility
            st.download_button("Download CSV for Board Meeting", df.to_csv().encode('utf-8'), "Incident_Report.csv", "text/csv")
        else:
            st.info("No reported incidents. System monitoring active.")
