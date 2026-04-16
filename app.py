import streamlit as st
import sqlite3
import pandas as pd
import re
import requests
import os
from datetime import datetime
import easyocr
import numpy as np
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="SafeSchool AI", layout="wide")
DB_FILE = "incidents.db"
HF_API_KEY = os.getenv("HF_API_KEY") # Set this in your Cloud Provider's Secrets

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reports 
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

def get_ocr_text(image):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(np.array(image))
    return " ".join([res[1] for res in result])

def analyze_incident(text, platform, duration):
    # API Chaining: Toxicity Analysis
    API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text}, timeout=5)
        toxicity = response.json()[0][0]["score"]
    except:
        toxicity = 0.5 # Fallback

    # Keyword Classification
    text_l = text.lower()
    b_type = "Verbal Abuse"
    if any(w in text_l for w in ["kill", "hurt", "find you"]): b_type = "Threat"
    elif any(w in text_l for w in ["ignore", "remove", "kick"]): b_type = "Social Exclusion"
    
    # Severity Logic
    severity = "LOW"
    if toxicity > 0.7 or b_type == "Threat": severity = "HIGH"
    elif toxicity > 0.4 or duration != "days": severity = "MEDIUM"

    actions = {"HIGH": "Immediate Intervention", "MEDIUM": "Counselor Meeting", "LOW": "Monitor"}
    
    return b_type, severity, actions[severity], toxicity

# --- UI LAYOUT ---
st.title("🚨 Cyberbullying Incident Response System")
tab1, tab2 = st.tabs(["📤 Submit Report", "📊 Counselor Dashboard"])

# --- TAB 1: STUDENT SUBMISSION ---
with tab1:
    st.header("Anonymous Incident Report")
    with st.form("report_form"):
        user_text = st.text_area("Describe what happened:")
        uploaded_file = st.file_uploader("Upload screenshot (Optional)", type=['png', 'jpg', 'jpeg'])
        
        col1, col2 = st.columns(2)
        with col1:
            platform = st.selectbox("Platform", ["WhatsApp", "Instagram", "Discord", "Other"])
        with col2:
            duration = st.selectbox("How long has this been happening?", ["days", "weeks", "months"])
        
        submit = st.form_submit_button("Submit Securely")

    if submit:
        with st.spinner("Processing..."):
            extracted_text = ""
            if uploaded_file:
                img = Image.open(uploaded_file)
                extracted_text = get_ocr_text(img)
            
            final_text = anonymize(user_text + " " + extracted_text)
            b_type, severity, action, tox_score = analyze_incident(final_text, platform, duration)
            
            # Save to SQLite
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO reports (timestamp, platform, type, severity, summary, raw_text, action) VALUES (?,?,?,?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d %H:%M"), platform, b_type, severity, 
                       f"{b_type} on {platform} for {duration}", final_text, action))
            conn.commit()
            conn.close()
            
            st.success("Report submitted successfully. Your identity is protected.")
            st.info(f"**Analysis Result:** Type: {b_type} | Severity: {severity}")

# --- TAB 2: COUNSELOR DASHBOARD ---
with tab2:
    st.header("Incident Management")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY id DESC", conn)
    conn.close()

    if not df.empty:
        # Analytics
        c1, c2 = st.columns(2)
        with c1:
            st.write("### Severity Distribution")
            st.bar_chart(df['severity'].value_counts())
        with c2:
            st.write("### Type Distribution")
            st.pie_chart(df['type'].value_counts())

        # Detailed Table
        st.write("### Recent Incidents")
        st.dataframe(df.drop(columns=['raw_text']), use_container_width=True)
    else:
        st.write("No reports filed yet.")
