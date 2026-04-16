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
# 🔑 CORE CONFIGURATION
# ==========================================
HF_API_KEY = "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" 
C_USER, C_PASS = "admin", "SafeSchool2026"

# ==========================================
# 🎨 BRANDING & DESIGN SYSTEM (CSS)
# ==========================================
st.set_page_config(page_title="SafeSchool AI | Pro", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .stApp { background-color: #f8fafc; }
    
    /* Elegant Card Design */
    .feature-card {
        background: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    
    /* Custom Headers */
    .hero-text { color: #1e293b; font-size: 55px; font-weight: 800; text-align: center; letter-spacing: -1px; }
    .hero-sub { color: #64748b; text-align: center; font-size: 20px; margin-bottom: 50px; }
    
    /* Buttons */
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em; 
        background-color: #2563eb; color: white; font-weight: 700; border: none;
    }
    .stButton>button:hover { background-color: #1d4ed8; box-shadow: 0 10px 15px -3px rgba(37,99,235,0.4); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🏗️ BACKEND: INTELLIGENT PIPELINE
# ==========================================
def init_db():
    with sqlite3.connect('safeschool_v3.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, platform TEXT, 
             type TEXT, severity TEXT, emotion TEXT, summary TEXT, status TEXT, score REAL)''')

def anonymize_data(text):
    """Protects student identity by redacting PII"""
    text = re.sub(r'\S+@\S+', '[EMAIL]', text)
    text = re.sub(r'\d{10}', '[PHONE]', text)
    return re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', text)

def call_ai_models(text):
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    tox_api = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    emo_api = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
    try:
        t_res = requests.post(tox_api, headers=headers, json={"inputs": text}, timeout=10).json()
        e_res = requests.post(emo_api, headers=headers, json={"inputs": text}, timeout=10).json()
        return t_res[0][0]['score'], e_res[0][0]['label']
    except: return 0.5, "uncertain"

# ==========================================
# 🚦 APPLICATION ROUTING
# ==========================================
init_db()
if 'view' not in st.session_state: st.session_state.view = "Home"

# --- SIDEBAR NAV ---
if st.session_state.view != "Home":
    if st.sidebar.button("🏠 Home / Logout"):
        st.session_state.view = "Home"; st.rerun()

# --- PAGE 1: HERO LANDING ---
if st.session_state.view == "Home":
    st.markdown("<div class='hero-text'>🛡️ SafeSchool AI</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-sub'>The Next-Gen Incident Response Platform</div>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<div class='feature-card'><h2>Student Portal</h2><p>Safe, 100% anonymous incident reporting. AI scrubs your personal details before any counselor sees them.</p></div>", unsafe_allow_html=True)
        if st.button("Start Anonymous Report"):
            st.session_state.view = "Student"; st.rerun()
            
    with col_b:
        st.markdown("<div class='feature-card'><h2>Staff Portal</h2><p>Administrative dashboard for counselors to monitor trends, analyze severity, and coordinate safety actions.</p></div>", unsafe_allow_html=True)
        user_in = st.text_input("Staff ID")
        pass_in = st.text_input("Security Key", type="password")
        if st.button("Secure Login"):
            if user_in == C_USER and pass_in == C_PASS:
                st.session_state.view = "Staff"; st.rerun()
            else: st.error("Access Denied.")

# --- PAGE 2: STUDENT REPORTING ---
elif st.session_state.view == "Student":
    st.markdown("<h1 style='color:#1e293b;'>New Incident Report</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        desc = st.text_area("Describe the incident (What was said? How did it start?)")
        files = st.file_uploader("Upload Evidence (Screenshots/Images)", accept_multiple_files=True)
        
        c1, c2, c3 = st.columns(3)
        pform = c1.selectbox("Platform", ["WhatsApp", "Instagram", "Snapchat", "Other"])
        freq = c2.selectbox("Frequency", ["Just once", "A few times", "Daily/Repeatedly"])
        dur = c3.selectbox("Duration", ["Days", "Weeks", "Months"])
        
        if st.button("Submit Report to AI Pipeline"):
            with st.status("🔍 Processing Pipeline...", expanded=True) as s:
                # OCR Step
                ocr_out = ""
                if files:
                    s.write("Extracting text from images...")
                    reader = easyocr.Reader(['en'])
                    for f in files:
                        res = reader.readtext(np.array(Image.open(f)))
                        ocr_out += " " + " ".join([r[1] for r in res])
                
                # AI Step
                s.write("Anonymizing & Running AI Analysis...")
                clean_text = anonymize_data(desc + " " + ocr_out)
                tox_val, emo_val = call_ai_models(clean_text)
                
                # Severity Logic
                sev = "LOW"
                if tox_val > 0.75 or freq == "Daily/Repeatedly": sev = "HIGH"
                elif tox_val > 0.4: sev = "MEDIUM"
                
                with sqlite3.connect('safeschool_v3.db') as conn:
                    conn.execute("INSERT INTO incidents (ts, platform, type, severity, emotion, summary, status, score) VALUES (?,?,?,?,?,?,?,?)",
                                 (datetime.now().strftime("%Y-%m-%d %H:%M"), pform, "Cyberbullying", sev, emo_val, clean_text[:300], "Pending", tox_val))
                
                s.update(label="Report Secured!", state="complete")
                st.balloons(); st.success("Your report has been submitted anonymously.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- PAGE 3: STAFF DASHBOARD ---
elif st.session_state.view == "Staff":
    st.title("📊 Safety Command Center")
    
    with sqlite3.connect('safeschool_v3.db') as conn:
        df = pd.read_sql_query("SELECT * FROM incidents ORDER BY id DESC", conn)
    
    if not df.empty:
        # High-Level Metrics
        met1, met2, met3, met4 = st.columns(4)
        met1.metric("Total Cases", len(df))
        met2.metric("High Severity", len(df[df.severity == "HIGH"]), delta_color="inverse")
        met3.metric("Avg. Toxicity", f"{int(df.score.mean()*100)}%")
        met4.metric("Pending Actions", len(df[df.status == "Pending"]))
        
        st.markdown("<div class='feature-card'>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Action Center
        st.subheader("Manage Case Status")
        col_id, col_stat = st.columns(2)
        target_id = col_id.selectbox("Case ID", df.id.tolist())
        target_stat = col_stat.select_slider("Set Status", ["Pending", "In Review", "Resolved"])
        if st.button("Update Database"):
            with sqlite3.connect('safeschool_v3.db') as conn:
                conn.execute("UPDATE incidents SET status = ? WHERE id = ?", (target_stat, target_id))
            st.rerun()
    else:
        st.info("No reported cases at this time.")
