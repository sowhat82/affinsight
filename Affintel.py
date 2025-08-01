# AI-Powered Reporting Assistant - Streamlit Prototype (v1)
# Project name: Affintel (by Affintive)

import streamlit as st
import pandas as pd
import requests
import os
import json
import re
import matplotlib.pyplot as plt
import seaborn as sns

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
    st.title("📊 Affintel – AI-Powered Reporting Assistant")
    st.subheader("🔐 Login")

    st.markdown("If you're a new user, create an account below:")
    with st.expander("Create a New Account"):
        new_username = st.text_input("New Username", key="new_user", value="sarah.johnson")
        new_password = st.text_input("New Password", type="password", key="new_pass", value="TechStart2024!")
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
    st.title("📊 Affintel – AI-Powered Reporting Assistant")
    if 'show_success' in st.session_state and st.session_state.show_success:
        st.success("Login successful. Welcome!")
        st.session_state.show_success = False

    if 'show_account_message' in st.session_state and st.session_state.show_account_message:
        st.success(f"✅ Account created and logged in!\n\n📂 Cloud folder initialized for user: '{st.session_state.username}'.\nAffintive staff will retrieve uploaded files from this folder.")
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

3. Finally, provide **Suggested Actions:** – 2-3 actionable suggestions for further analysis or follow-up based on the generated insights.

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

    # --- ONBOARDING INSIGHTS FUNCTION ---
    def generate_onboarding_insights(business_name, contact_person, industry, annual_revenue, num_employees, key_challenges):
        prompt = f"""
You are a business consultant analyzing a new client's onboarding information. Generate professional insights for Affintive staff.

Client: {business_name} | Industry: {industry} | Revenue: ${annual_revenue:,.0f} | Staff: {num_employees} | Challenges: {key_challenges}

Provide structured insights in this format:

**Pain Points:** (3 specific points, 10-20 words each)
**Staff Focus:** (3 actionable recommendations, 10-20 words each)
**Risk Assessment:** (2-3 sentences with specific risk factors and opportunities)

Be professional, specific, and reference the actual client data provided.
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
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        continue
                else:
                    continue
            except Exception as e:
                st.warning(f"❌ Model failed: {model} – {e}")
                continue

        # Fallback to simulated insights if API fails
        return """**Pain Points:**
• Cash flow volatility during project-based revenue cycles affecting working capital
• Operational scaling challenges with current 12-person team structure and growth demands
• Client expectation management and project timeline pressures impacting delivery quality

**Staff Focus:**
• Implement robust cash flow forecasting and working capital management solutions
• Develop scalable operational frameworks and team productivity optimization strategies  
• Establish comprehensive project management and client communication protocols

**Risk Assessment:**
Medium-risk engagement with strong revenue foundation ($850K annually) but typical growing tech company challenges. Cash flow volatility presents immediate concern requiring attention. Growth trajectory suggests good long-term partnership potential."""

    # --- FILE UPLOAD & DATA PREVIEW ---
    def upload_and_preview():
        st.subheader("Upload your financial data or fetch from Xero")

        st.markdown("""
        **Choose your data source:**
        - Fetch current year data from Xero.
        - Upload your own Excel or CSV file.
        """)

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

            if st.button("Generate Insights"):
                with st.spinner("Analyzing..."):
                    insights = generate_insights(df, None)  # Pass None instead of insight_option
                    st.session_state["last_insights"] = insights

                # Dynamically display chart based on data structure
                display_chart(df)

        # Display relevant mock data if available
        if "mock_data" in st.session_state:
            st.write("Preview of fetched data:")
            st.dataframe(st.session_state["mock_data"][insight_option])

            if st.button("Generate Insights for Xero Data"):
                with st.spinner("Analyzing..."):
                    insights = generate_insights(st.session_state["mock_data"][insight_option], insight_option)
                    st.session_state["last_insights"] = insights

                # Display chart after insights are generated
                display_chart(st.session_state["mock_data"][insight_option])

        # Display insights and charts after the initial options for data source
        if "last_insights" in st.session_state:
            st.subheader("AI-Generated Insights")
            for section in st.session_state["last_insights"].split("\n"):
                if section.strip():
                    # Display raw section using st.text to avoid Markdown processing
                    st.text(section.strip())

            if "last_model_used" in st.session_state:
                st.caption(f"Model used: {st.session_state['last_model_used']}")

            if st.button("Sync to Xero"):
                st.success("✅ Data has been synced to Xero. A copy of the data has been forwarded to Affintive's internal system.")

    def display_chart(data, insight_option=None):
        """Dynamically analyze the data and display the best chart."""
        st.subheader("Dynamic Data Analysis")

        # Identify numerical and categorical columns
        numerical_columns = data.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = data.select_dtypes(include=['object', 'category']).columns.tolist()

        if len(numerical_columns) >= 1 and len(categorical_columns) >= 1:
            # Use pie chart only if the categorical column has fewer than 10 unique values and the insight option suggests categorical analysis
            if insight_option == "Claims & expenses" and data[categorical_columns[0]].nunique() <= 10:
                st.subheader("Pie Chart")
                fig, ax = plt.subplots()
                data.groupby(categorical_columns[0])[numerical_columns[0]].sum().plot(kind="pie", autopct="%1.1f%%", ax=ax)
                ax.set_ylabel("")
                ax.set_title(f"Proportion of {numerical_columns[0]} by {categorical_columns[0]}")
                st.pyplot(fig)
            else:
                st.subheader("Bar Chart")
                fig, ax = plt.subplots()
                sns.barplot(x=categorical_columns[0], y=numerical_columns[0], data=data, ax=ax)
                ax.set_title(f"{numerical_columns[0]} by {categorical_columns[0]}")
                st.pyplot(fig)

        elif len(numerical_columns) >= 1 and 'Date' in data.columns:
            # Line chart for time-series data
            st.subheader("Line Chart")
            fig, ax = plt.subplots()
            sns.lineplot(x='Date', y=numerical_columns[0], data=data, marker="o", ax=ax)
            ax.set_title(f"{numerical_columns[0]} Over Time")
            st.pyplot(fig)

        else:
            st.error("Unable to determine the best chart for the uploaded data.")

    # --- ONBOARDING CHECKLIST PAGE ---
    def onboarding_checklist():
        st.subheader("📂 Client Onboarding Form")

        st.markdown("**Client Information Entry:**")
        st.caption("This section is filled out by the client during onboarding")

        # Add fields from the onboarding form with default mock data
        business_name = st.text_input("Business Name", value="TechStart Solutions Pty Ltd")
        contact_person = st.text_input("Contact Person", value="Sarah Johnson")
        email = st.text_input("Email Address", value="sarah.johnson@techstart.com.au")
        phone = st.text_input("Phone Number", value="+61 2 8765 4321")
        industry = st.text_input("Industry", value="Software Development & IT Services")
        annual_revenue = st.number_input("Annual Revenue", min_value=0.0, step=0.01, value=850000.00)
        num_employees = st.number_input("Number of Employees", min_value=0, step=1, value=12)
        key_challenges = st.text_area("Key Challenges (e.g., cash flow, growth, etc.)", 
                                    value="Cash flow management during project cycles, scaling team efficiently, managing client expectations and project timelines, need better financial forecasting tools")

        # Submit button for client
        if st.button("Submit Client Information", type="primary"):
            st.success("✅ Client information submitted successfully!")
            st.session_state["client_data_submitted"] = True
            st.session_state["client_data"] = {
                "business_name": business_name,
                "contact_person": contact_person,
                "industry": industry,
                "annual_revenue": annual_revenue,
                "num_employees": num_employees,
                "key_challenges": key_challenges
            }

        st.markdown("---")

        # Staff section - only show after client data is submitted
        if st.session_state.get("client_data_submitted", False):
            st.subheader("🔍 Affintive Staff Analysis Section")
            st.caption("This section is used by Affintive staff to analyze client data")
            
            client_data = st.session_state.get("client_data", {})
            
            # Display client data summary for staff
            with st.expander("📋 Client Data Summary", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Business:** {client_data.get('business_name', 'N/A')}")
                    st.write(f"**Industry:** {client_data.get('industry', 'N/A')}")
                    st.write(f"**Revenue:** ${client_data.get('annual_revenue', 0):,.2f}")
                with col2:
                    st.write(f"**Contact:** {client_data.get('contact_person', 'N/A')}")
                    st.write(f"**Employees:** {client_data.get('num_employees', 0)}")
                
                st.write(f"**Key Challenges:** {client_data.get('key_challenges', 'N/A')}")

            # Staff analysis button
            if st.button("🔍 Generate Customer's Pain Point Analysis", help="For Affintive staff use only"):
                with st.spinner("Analyzing client data..."):
                    # Generate actual AI insights based on the provided data
                    insights = generate_onboarding_insights(
                        client_data.get('business_name', ''),
                        client_data.get('contact_person', ''),
                        client_data.get('industry', ''),
                        client_data.get('annual_revenue', 0),
                        client_data.get('num_employees', 0),
                        client_data.get('key_challenges', '')
                    )
                    
                    st.subheader("🎯 AI-Generated Staff Insights")
                    # Display the insights with proper formatting
                    for section in insights.split("\n"):
                        if section.strip():
                            st.text(section.strip())

                    st.info("⚠️ **Staff Reminder:** Ensure proper due diligence is conducted before making recommendations to client.")

        else:
            st.info("👆 Please submit client information above to proceed with staff analysis")

        st.markdown("---")
        st.caption("💡 This prototype demonstrates the client-to-staff workflow. Document collection can be handled separately in the full implementation.")

    # --- MAIN APP ROUTING ---
    st.set_page_config(page_title="Affintel", layout="centered")

    if page == "📂 Onboarding Checklist":
        onboarding_checklist()

    elif page == "📊 Financial Insights":
        upload_and_preview()
        st.markdown("""
        ---
        **Security note:** Your data is transferred securely and is not stored.
        """)
