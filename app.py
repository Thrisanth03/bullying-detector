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
# 🔑 CONFIG & AI MODELS
# ==========================================
HF_API_KEY = "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"

@st.cache_resource
def load_ocr():
    # Cache the model so it only loads once, saving RAM
    return easyocr.Reader(['en'], gpu=False)

def call_ai(text):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    api = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    try:
        res = requests.post(api, headers=headers, json={"inputs": text}, timeout=10).json()
        return res[0][0]['score']
    except: return 0.0

# ==========================================
# 🎨 UI STYLING
# ==========================================
st.set_page_config(page_title="SafeSchool AI", page_icon="🛡️")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: white; }
    .card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; }
    .stButton>button { background: #2563eb; color: white; border-radius: 10px; width: 100%; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🚦 APP LOGIC
# ==========================================
if 'view' not in st.session_state: st.session_state.view = "Student"

# Database Init
conn = sqlite3.connect('safeschool.db', check_same_thread=False)
conn.execute('CREATE TABLE IF NOT EXISTS reports (ts TEXT, platform TEXT, text TEXT, score REAL)')

st.title("🛡️ SafeSchool AI")

if st.session_state.view == "Student":
    st.markdown("### 📝 Incident Analysis Terminal")
    
    with st.container():
        msg = st.text_area("What happened?")
        imgs = st.file_uploader("Upload Screenshots", accept_multiple_files=True)
        plat = st.selectbox("Platform", ["WhatsApp", "Instagram", "Discord", "Other"])
        
        if st.button("Analyze & Submit Report"):
            with st.spinner("AI Processing..."):
                full_text = msg
                if imgs:
                    reader = load_ocr()
                    for img in imgs:
                        res = reader.readtext(np.array(Image.open(img)))
                        full_text += " " + " ".join([r[1] for r in res])
                
                # Anonymize
                clean_text = re.sub(r'\d{10}', '[PHONE]', full_text)
                score = call_ai(clean_text)
                
                # Save
                ts = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.execute('INSERT INTO reports VALUES (?,?,?,?)', (ts, plat, clean_text[:200], score))
                conn.commit()
                
                st.success("Report submitted anonymously.")
                if score > 0.8: st.warning("🚨 High priority alert sent to counselor.")
                st.balloons()

    st.divider()
    st.subheader("🆘 Crisis Support")
    if st.button("🚨 IMMEDIATE HELP"):
        st.error("Alarm triggered. A counselor has been notified.")

    if st.sidebar.button("Staff Login"):
        st.session_state.view = "Staff"; st.rerun()

elif st.session_state.view == "Staff":
    st.sidebar.button("Back to Student Portal", on_click=lambda: st.session_state.update({"view": "Student"}))
    st.header("📊 Admin Dashboard")
    df = pd.read_sql_query("SELECT * FROM reports ORDER BY ts DESC", conn)
    st.dataframe(df, use_container_width=True)
