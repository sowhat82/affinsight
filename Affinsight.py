# AI-Powered Reporting Assistant - Streamlit Prototype (v1)
# Project name: Affinsight (by Affintive)

import streamlit as st
import pandas as pd
import requests
import os
import json
import re

from dotenv import load_dotenv
load_dotenv()

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

    st.markdown("If you're a new user, create an account below:")
    with st.expander("Create a New Account"):
        new_username = st.text_input("New Username", key="new_user")
        new_password = st.text_input("New Password", type="password", key="new_pass")
        if st.button("Register"):
            st.session_state.logged_in = True
            st.session_state.username = new_username
            st.session_state.show_success = True
            st.session_state.show_account_message = True
            st.rerun()

    st.markdown("---")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.show_success = True
            st.rerun()
    st.stop()

if st.session_state.logged_in:
    st.image("affintive_logo.png", width=200)
    st.title("📊 Affinsight – AI-Powered Reporting Assistant")
    if 'show_success' in st.session_state and st.session_state.show_success:
        st.success("Login successful. Welcome!")
        st.session_state.show_success = False

    if 'show_account_message' in st.session_state and st.session_state.show_account_message:
        st.success(f"✅ Account created and logged in!\n\n📂 Simulated cloud folder initialized for user: '{st.session_state.username}'.\nAffintive staff will retrieve uploaded files from this folder.")
        st.session_state.show_account_message = False

    # --- PAGE SELECTION ---
    page = st.sidebar.radio("Navigation", ["📂 Onboarding Checklist", "📊 Financial Insights"])

    # --- LLM PROMPT FUNCTION ---
    def generate_insights(data, option):
        # Remove column filtering and send the entire parsed data to the model
        if option == "Payroll only":
            prompt_context = "Analyze payroll data, focusing on salary distribution, bonuses, and any notable patterns or trends."
        elif option == "Claims & expenses":
            prompt_context = "Analyze claims and expenses, identifying categories with the highest costs, trends over time, and potential areas for cost optimization."
        elif option == "Revenue":
            prompt_context = "Analyze revenue data, focusing on monthly growth, seasonal patterns, and overall performance trends."
        else:
            prompt_context = ""  # Default to empty if option is None or unrecognized

        # Handle None for option in generate_insights
        if option is None:
            option_description = "uploaded financial"
        else:
            option_description = option.lower()

        # Use the entire data without filtering
        column_summary = ", ".join(data.columns)
        prompt_stats = ""

        for column in data.columns:
            values = ", ".join(str(x) for x in data[column].tolist())
            prompt_stats += f"{column}: {values}\n"

        prompt = f"""
You are a data analyst tasked with generating insights for SME management. Based on the provided {option_description} data, do the following:

1. Write an **Executive Summary:** (1-2 sentences) that highlights the most impactful findings or recommendations. This summary should help busy executives quickly focus their attention on the most critical issues or opportunities.

2. Then, follow with **Key Insights:** – 3 factual and helpful bullet-point insights based strictly on the uploaded data. {prompt_context}

Data (CSV preview and summary stats below):
{prompt_stats}

Raw data table:
{data.to_csv(index=False)}
"""

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        for model in models:
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

                        # Debug: Display raw response from OpenRouter
                        st.subheader("Raw Response from OpenRouter")
                        st.json(result)

                        return result['choices'][0]['message']['content'].strip()
                    else:
                        continue
                else:
                    continue
            except Exception as e:
                st.warning(f"❌ Model failed: {model} – {e}")
                continue

        st.error("All models are currently unavailable or rate-limited. Please try again later.")
        return ""

    # --- FILE UPLOAD & DATA PREVIEW ---
    def upload_and_preview():
        st.subheader("Upload your financial data or fetch from Xero")

        # Add options for filtering insights
        insight_option = st.radio(
            "Select the type of insights to generate:",
            ["Payroll only", "Claims & expenses", "Revenue"],
            index=0
        )

        # Simulate fetching current year data from Xero
        if st.button("Fetch Current Year Data from Xero"):
            st.success("✅ Current year data fetched from Xero. Insights will be generated based on this data.")

            # Mock data for preview
            st.session_state["mock_data"] = {
                "Payroll only": pd.DataFrame({
                    "Employee": ["Alice", "Bob", "Charlie"],
                    "Salary": [5000, 4500, 4800],
                    "Bonuses": [500, 400, 450]
                }),
                "Claims & expenses": pd.DataFrame({
                    "Category": ["Travel", "Office Supplies", "Utilities"],
                    "Amount": [1200, 800, 600]
                }),
                "Revenue": pd.DataFrame({
                    "Month": ["January", "February", "March"],
                    "Revenue": [10000, 12000, 15000]
                })
            }

        # Display relevant mock data if available
        if "mock_data" in st.session_state:
            st.write("Preview of fetched data:")
            st.dataframe(st.session_state["mock_data"][insight_option])

            if st.button("Generate Insights for Xero Data"):
                with st.spinner("Analyzing..."):
                    insights = generate_insights(st.session_state["mock_data"][insight_option], insight_option)
                    st.session_state["last_insights"] = insights

        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    import openpyxl
                    df = pd.read_excel(uploaded_file, engine="openpyxl")
            except ImportError:
                st.error("The 'openpyxl' package is required to read Excel files. Please install it by adding 'openpyxl' to your requirements.txt.")
                return None

            st.write("Preview of uploaded data:")
            st.dataframe(df.head())

            # Exclude insight_option from the prompt for Excel uploads
            if uploaded_file:
                column_summary = ", ".join(df.columns)
                prompt_stats = ""

                for column in df.columns:
                    values = ", ".join(str(x) for x in df[column].tolist())
                    prompt_stats += f"{column}: {values}\n"

                prompt = f"""
You are a data analyst tasked with generating insights for SME management. Based on the provided financial data, do the following:

1. Write an **Executive Summary:** (1-2 sentences) that highlights the most impactful findings or recommendations. This summary should help busy executives quickly focus their attention on the most critical issues or opportunities.

2. Then, follow with **Key Insights:** – 3 factual and helpful bullet-point insights based strictly on the uploaded data.

Data (CSV preview and summary stats below):
{prompt_stats}

Raw data table:
{df.to_csv(index=False)}
"""

                if st.button("Generate Insights"):
                    with st.spinner("Analyzing..."):
                        insights = generate_insights(df, None)  # Pass None instead of insight_option
                        st.session_state["last_insights"] = insights

        if "last_insights" in st.session_state:
            st.subheader("AI-Generated Insights")
            for section in st.session_state["last_insights"].split("\n"):
                if section.strip():
                    if section.strip().lower().startswith("executive summary"):
                        st.markdown(f"\n**{section.strip()}**\n")
                    elif section.strip().lower().startswith("key insights"):
                        st.markdown(f"\n**{section.strip()}**\n")
                    elif section.strip().startswith("-"):
                        st.markdown(section.strip())
                    else:
                        st.markdown(section.strip())
            if "last_model_used" in st.session_state:
                st.caption(f"Model used: {st.session_state['last_model_used']}")

            if st.button("Sync to Xero"):
                st.success("✅ Data has been (simulated) synced to Xero. A copy of the data has been forwarded to Affintive's internal system.")

    # --- ONBOARDING CHECKLIST PAGE ---
    def onboarding_checklist():
        st.subheader("📂 Onboarding Checklist")

        checklist_items = [
            "Business Registration Documents",
            "Past 3 Months Bank Statements",
            "Previous P&L Statements",
            "Payroll Summary",
            "Outstanding Invoices / Receivables"
        ]

        for item in checklist_items:
            st.markdown(f"**{item}**")
            uploaded = st.file_uploader(f"Upload {item}", key=item)
            if uploaded:
                st.success(f"✅ '{item}' uploaded. Affintive account manager notified.")

    # --- MAIN APP ROUTING ---
    st.set_page_config(page_title="Affinsight", layout="centered")

    if page == "📂 Onboarding Checklist":
        onboarding_checklist()

    elif page == "📊 Financial Insights":
        upload_and_preview()
        st.markdown("""
        ---
        **Security note:** Your data is transferred securely and is not stored.
        """)
