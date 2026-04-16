import streamlit as st
from transformers import pipeline
import re
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Cyberbullying AI", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    h1 {color: #FF4B4B;}
    </style>
""", unsafe_allow_html=True)

st.title("🚨 Cyberbullying Incident Response Assistant")

# ---------------- MODEL ----------------
@st.cache_resource
def load_model():
    return pipeline("sentiment-analysis")

classifier = load_model()

# ---------------- DATABASE ----------------
conn = sqlite3.connect("reports.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    severity TEXT,
    summary TEXT,
    action TEXT,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- FUNCTIONS ----------------
def anonymize(text):
    text = re.sub(r'\b[A-Z][a-z]{2,}\b', '[REDACTED]', text)
    text = re.sub(r'\d{10}', '[REDACTED]', text)
    return text

def calculate_severity(label, score):
    if label == "NEGATIVE" and score > 0.7:
        return "HIGH"
    elif label == "NEGATIVE":
        return "MEDIUM"
    return "LOW"

def get_action(severity):
    if severity == "HIGH":
        return "Immediate intervention"
    elif severity == "MEDIUM":
        return "Counselor session"
    return "Monitor"

def simple_summary(text):
    return text[:100]

# ---------------- INPUT UI ----------------
col1, col2 = st.columns(2)

with col1:
    text = st.text_area("📝 Enter Report")

with col2:
    st.markdown("### ℹ️ Instructions")
    st.write("Describe the incident clearly. System will analyze risk level.")

# ---------------- ANALYZE ----------------
if st.button("🔍 Analyze"):
    if text.strip() == "":
        st.warning("Please enter a report")
    else:
        clean = anonymize(text)

        result = classifier(clean)[0]
        severity = calculate_severity(result['label'], result['score'])

        summary = simple_summary(clean)
        action = get_action(severity)

        cursor.execute("""
        INSERT INTO reports (text, severity, summary, action, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """, (clean, severity, summary, action, str(datetime.now())))
        conn.commit()

        st.subheader("📊 Analysis Result")

        colA, colB, colC = st.columns(3)

        with colA:
            st.metric("Severity", severity)

        with colB:
            st.metric("Confidence", round(result['score'], 2))

        with colC:
            st.metric("Action", action)

        if severity == "HIGH":
            st.error("🚨 Immediate Attention Required")
        elif severity == "MEDIUM":
            st.warning("⚠️ Monitor & Counsel")
        else:
            st.success("✅ Low Risk")

        st.write("### 🧾 Summary")
        st.info(summary)

# ---------------- DASHBOARD ----------------
st.subheader("📊 Incident Dashboard")

rows = cursor.execute("SELECT * FROM reports").fetchall()

high = sum(1 for r in rows if r[2] == "HIGH")
medium = sum(1 for r in rows if r[2] == "MEDIUM")
low = sum(1 for r in rows if r[2] == "LOW")

col1, col2, col3 = st.columns(3)

col1.metric("🔴 High", high)
col2.metric("🟡 Medium", medium)
col3.metric("🟢 Low", low)

st.markdown("### 📜 Recent Reports")

for row in rows[-5:][::-1]:
    st.write(f"🕒 {row[5]} | **{row[2]}** | {row[3]}")
