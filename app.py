import streamlit as st
import pandas as pd
import sqlite3
import re
import requests
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# --- CONFIG & STYLING ---
st.set_page_config(page_title="SafeSchool AI", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .report-card { background: white; padding: 25px; border-radius: 15px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .counselor-stat { text-align: center; padding: 20px; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('incidents.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidents 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, platform TEXT, 
                  type TEXT, severity TEXT, summary TEXT, raw_text TEXT, action TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- BACKEND LOGIC ---
def anonymize(text):
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    text = re.sub(r'\d{10}', '[PHONE]', text)
    text = re.sub(r'\b[A-Z][a-z]+\b', '[NAME]', text)
    return text

def send_email_alert(data):
    try:
        msg = EmailMessage()
        msg.set_content(f"High Severity Incident Detected!\n\nSummary: {data['summary']}\nType: {data['type']}\nAction: {data['action']}")
        msg['Subject'] = f"🚨 URGENT: High Severity Incident - {data['type']}"
        msg['From'] = st.secrets["SMTP_USER"]
        msg['To'] = st.secrets["COUNSELOR_EMAIL"]
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASS"])
            smtp.send_message(msg)
    except Exception as e:
        print(f"Email failed: {e}")

def run_analysis(text, image_count, platform, duration):
    # 1. Toxicity Check (Cloud AI)
    API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=5).json()
        score = response[0][0]['score']
    except:
        score = 0.5

    # 2. Logic Gates
    b_type = "Verbal Abuse"
    if any(w in text.lower() for w in ["kill", "threat", "hurt"]): b_type = "Threat"
    
    # Severity Logic
    severity = "LOW"
    if score > 0.8 or b_type == "Threat": severity = "HIGH"
    elif score > 0.4 or image_count > 2 or duration != "days": severity = "MEDIUM"
    
    actions = {"HIGH": "Immediate intervention + parent alert", "MEDIUM": "Counselor meeting", "LOW": "Monitor"}
    
    return {"type": b_type, "severity": severity, "score": score, "action": actions[severity]}

# --- AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False

# --- UI LAYOUT ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/1162/1162933.png", width=100)
        st.title("SafeSchool Portal")
        mode = st.tabs(["Student Portal", "Counselor Portal"])
        
        with mode[0]:
            if st.button("Enter Anonymously", use_container_width=True):
                st.session_state.role = "student"
                st.session_state.auth = True
                st.rerun()
                
        with mode[1]:
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                if user == st.secrets["C_USER"] and pw == st.secrets["C_PASS"]:
                    st.session_state.role = "counselor"
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Invalid Credentials")

else:
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

    if st.session_state.role == "student":
        st.header("📝 Submit a Secure Report")
        with st.container():
            st.markdown("<div class='report-card'>", unsafe_allow_html=True)
            u_text = st.text_area("What happened? (Text is optional if image is provided)")
            u_img = st.file_uploader("Upload Evidence Screenshots", accept_multiple_files=True)
            
            c1, c2 = st.columns(2)
            with c1: plat = st.selectbox("Platform", ["WhatsApp", "Instagram", "School App", "Discord"])
            with c2: dur = st.select_slider("How long has this been happening?", ["days", "weeks", "months"])
            
            if st.button("Submit Anonymous Report", use_container_width=True):
                with st.spinner("Processing with Cloud AI..."):
                    # OCR Logic
                    extracted = ""
                    if u_img:
                        reader = easyocr.Reader(['en'])
                        for img_file in u_img:
                            img = Image.open(img_file)
                            res = reader.readtext(np.array(img))
                            extracted += " " + " ".join([r[1] for r in res])
                    
                    full_text = anonymize(u_text + " " + extracted)
                    results = run_analysis(full_text, len(u_img), plat, dur)
                    
                    # Store Data
                    conn = sqlite3.connect('incidents.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO incidents (timestamp, platform, type, severity, summary, raw_text, action) VALUES (?,?,?,?,?,?,?)",
                              (datetime.now().strftime("%Y-%m-%d %H:%M"), plat, results['type'], results['severity'], 
                               f"Incident on {plat} duration {dur}", full_text, results['action']))
                    conn.commit()
                    conn.close()
                    
                    if results['severity'] == "HIGH": send_email_alert(results)
                    
                    st.success("Report Submitted. Your identity is hidden.")
                    st.balloons()
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.header("📊 Counselor Dashboard")
        conn = sqlite3.connect('incidents.db')
        df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
        conn.close()
        
        if not df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Cases", len(df))
            m2.metric("High Severity", len(df[df['severity'] == "HIGH"]))
            m3.metric("Common Type", df['type'].mode()[0])
            
            st.subheader("Incident Logs")
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Export Incident Report", data=csv, file_name="reports.csv", mime="text/csv")
        else:
            st.info("No incidents reported yet.")
