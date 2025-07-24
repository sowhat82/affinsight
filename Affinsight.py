# AI-Powered Reporting Assistant - Streamlit Prototype (v1)
# Project name: Affinsight (by Affintive)

import streamlit as st
import pandas as pd
import requests
import os
import json

# --- CONFIGURATION ---
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Load models from external JSON file (models_config.json)
with open("models_config.json") as f:
    models = json.load(f).get("models", [])

# --- SIMULATED LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.image("affintive_logo.png", width=200)
    st.title("📊 Affinsight – AI-Powered Reporting Assistant")
    st.subheader("🔐 Login Simulation")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            st.session_state.logged_in = True
            st.session_state.show_success = True
            st.rerun()
    st.stop()

if st.session_state.logged_in:
    st.image("affintive_logo.png", width=200)
    st.title("📊 Affinsight – AI-Powered Reporting Assistant")
    if 'show_success' in st.session_state and st.session_state.show_success:
        st.success("Login successful. Welcome!")
        st.session_state.show_success = False

# --- LLM PROMPT FUNCTION ---
def generate_insights(data):
    column_summary = ", ".join(data.columns)
    prompt_stats = ""

    if 'Revenue' in data.columns:
        values = ", ".join(str(x) for x in data['Revenue'].tolist())
        prompt_stats += f"Revenue by month: {values}\n"
    if 'Operating Expenses' in data.columns:
        values = ", ".join(str(x) for x in data['Operating Expenses'].tolist())
        prompt_stats += f"Operating Expenses by month: {values}\n"
    if 'Net Profit' in data.columns:
        values = ", ".join(str(x) for x in data['Net Profit'].tolist())
        prompt_stats += f"Net Profit by month: {values}\n"

    prompt = f"""
You are a financial analyst. Review the client's financial data and write 3 useful bullet-point insights about their performance.
Focus on revenue, expenses, and profit.
Use only the facts from the data below. Avoid assumptions.

{prompt_stats}
Data:
{data.to_csv(index=False)}
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in models:
#        st.write(f"🔍 Trying model: {model}")
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(OPENROUTER_API_URL, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('choices'):
                    st.session_state["last_model_used"] = model
                    return result['choices'][0]['message']['content'].strip()
                else:
                    continue
            else:
#                st.warning(f"⚠️ Model {model} returned status code {response.status_code}")
                continue
        except Exception as e:
            st.warning(f"❌ Model failed: {model} – {e}")
            continue

    st.error("All models are currently unavailable or rate-limited. Please try again later.")
    return ""

# --- FILE UPLOAD & DATA PREVIEW ---
def upload_and_preview():
    st.subheader("Upload your financial data")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.write("Preview of uploaded data:")
        st.dataframe(df.head())

        if st.button("Generate Insights"):
            with st.spinner("Analyzing..."):
                insights = generate_insights(df)
                st.subheader("AI-Generated Insights")
                st.text(insights)
                if "last_model_used" in st.session_state:
                    st.caption(f"Model used: {st.session_state['last_model_used']}")

# --- MAIN APP ---
st.set_page_config(page_title="Affinsight", layout="centered")

if st.session_state.get('logged_in'):
    upload_and_preview()
    st.markdown("""
    ---
    **Security note:** Your data is transferred securely and is not stored.
    """)
