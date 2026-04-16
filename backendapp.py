from fastapi import FastAPI
from pydantic import BaseModel
import requests
import re
import os

app = FastAPI()

HF_API_KEY = os.getenv("HF_API_KEY")

# ---------------- INPUT MODEL ----------------
class Report(BaseModel):
    text: str
    frequency: int
    duration: str

# ---------------- FUNCTIONS ----------------

def anonymize(text):
    text = re.sub(r'\b[A-Z][a-z]{2,}\b', '[REDACTED]', text)
    text = re.sub(r'\d{10}', '[REDACTED]', text)
    return text

def get_toxicity(text):
    API_URL = "https://api-inference.huggingface.co/models/unitary/toxic-bert"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}

    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": text})
        return response.json()[0][0]["score"]
    except:
        return 0.5

def classify_type(text):
    text = text.lower()
    if "kill" in text or "threat" in text:
        return "Threat"
    elif "stupid" in text or "idiot" in text:
        return "Verbal"
    elif "ignore" in text:
        return "Exclusion"
    return "General"

def calculate_severity(toxicity, b_type):
    if toxicity > 0.8 or b_type == "Threat":
        return "HIGH"
    elif toxicity > 0.4:
        return "MEDIUM"
    return "LOW"

def get_action(severity):
    if severity == "HIGH":
        return "Immediate intervention"
    elif severity == "MEDIUM":
        return "Counselor session"
    return "Monitor"

# ---------------- API ----------------

@app.post("/analyze")
def analyze(report: Report):
    clean = anonymize(report.text)

    # API chaining → Hugging Face
    toxicity = get_toxicity(clean)

    b_type = classify_type(clean)
    severity = calculate_severity(toxicity, b_type)
    action = get_action(severity)

    return {
        "type": b_type,
        "toxicity": toxicity,
        "severity": severity,
        "summary": clean[:120],
        "action": action
    }
