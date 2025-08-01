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
    page = st.sidebar.radio("Navigation", ["📂 Onboarding Checklist", "📊 Financial Insights", "🔔 Alerts Workflow", "📋 Client Summary"])
    
    # SharePoint connection status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📁 Data Sources:**")
    
    # Xero status (always available in demo)
    st.sidebar.markdown("✅ Xero: Connected")
    
    # SharePoint status
    if st.session_state.get("sharepoint_connected", False):
        st.sidebar.markdown("✅ SharePoint: Connected")
        if st.session_state.get("sharepoint_last_sync"):
            st.sidebar.caption(f"Last sync: {st.session_state['sharepoint_last_sync']}")
        
        # Show sync reminder in sidebar if needed
        st.sidebar.caption("⚠️ 4 days since last update")
    else:
        st.sidebar.markdown("🔌 SharePoint: Not connected")
        st.sidebar.caption("Connect in Financial Insights")
    
    st.sidebar.markdown("📤 Manual Upload: Available")

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

    # --- CLIENT SUMMARY FUNCTION ---
    def generate_client_summary(business_name, contact_person, industry, annual_revenue, num_employees, key_challenges):
        prompt = f"""
You are a senior business consultant creating a one-page client summary for Affintive staff preparing for client meetings.

Client: {business_name} | Industry: {industry} | Revenue: ${annual_revenue:,.0f} | Staff: {num_employees} | Challenges: {key_challenges}

Generate a comprehensive client summary in this exact format:

**Business Profile:**
• Company Size: [Classify as Micro/Small/Medium/Large based on revenue and employees]
• Industry Position: [Brief assessment of their market position and competitive landscape]
• Financial Health: [Revenue assessment and growth indicators]

**Digital Maturity Assessment:**
• Technology Adoption: [Rate as Basic/Developing/Advanced/Sophisticated - 1-2 sentences]
• Systems Integration: [Assessment of current digital infrastructure and integration needs]
• Automation Readiness: [Evaluation of potential for process automation and digital transformation]

**Key Watch Areas:**
• Priority 1: [Most critical area requiring immediate attention]
• Priority 2: [Secondary concern that needs monitoring]
• Priority 3: [Third area of focus for medium-term planning]

**Risk & Opportunity Matrix:**
• Primary Risk: [Main business risk to be aware of in interactions]
• Growth Opportunity: [Key opportunity for service expansion or upselling]
• Partnership Potential: [Assessment of long-term relationship prospects]

**Meeting Preparation Notes:**
• Discussion Topics: [2-3 key areas to focus on in upcoming meetings]
• Value Propositions: [Specific Affintive services most relevant to this client]
• Relationship Status: [Current engagement level and next steps for relationship building]

Keep each point concise (10-25 words) and professionally actionable for staff preparation.
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

        # Fallback to simulated summary if API fails
        return """**Business Profile:**
• Company Size: Small business with solid revenue foundation and efficient team structure
• Industry Position: Competitive software development sector with established client relationships and growth trajectory
• Financial Health: Strong $850K annual revenue indicates stable operations with scaling potential

**Digital Maturity Assessment:**
• Technology Adoption: Developing - Using standard development tools but lacking advanced analytics and automation
• Systems Integration: Basic integration with room for improvement in workflow optimization and data connectivity
• Automation Readiness: Good potential for implementing automated reporting, project management, and client communication systems

**Key Watch Areas:**
• Priority 1: Cash flow management during project-based revenue cycles affecting working capital stability
• Priority 2: Team scaling challenges with current 12-person structure requiring operational framework development
• Priority 3: Client expectation management and project delivery timelines needing systematic improvement processes

**Risk & Opportunity Matrix:**
• Primary Risk: Cash flow volatility could impact growth investments and operational stability during lean periods
• Growth Opportunity: Strong demand for financial forecasting and operational optimization consulting services
• Partnership Potential: High - established business with growth mindset and willingness to invest in improvements

**Meeting Preparation Notes:**
• Discussion Topics: Financial forecasting solutions, operational scaling frameworks, and project management optimization systems
• Value Propositions: Cash flow management tools, team productivity consulting, and automated reporting solutions
• Relationship Status: Early engagement phase with high potential for comprehensive service partnership and long-term growth"""

    # --- FILE UPLOAD & DATA PREVIEW ---
    def upload_and_preview():
        st.subheader("Upload your financial data or fetch from multiple sources")

        st.markdown("""
        **Choose your data source:**
        - Fetch current year data from Xero.
        - Synchronize with your SharePoint folder.
        - Upload your own Excel or CSV file manually.
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

        # SharePoint synchronization section
        st.markdown("---")
        st.markdown("**📁 SharePoint Integration:**")
        
        # SharePoint connection status
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**SharePoint Folder Status:**")
            if "sharepoint_connected" not in st.session_state:
                st.session_state["sharepoint_connected"] = False
            
            if st.session_state["sharepoint_connected"]:
                st.success("🔗 Connected to SharePoint folder: `/Financial Data/Monthly Reports`")
                st.caption("Last sync: 2025-07-28 14:30 (4 days ago)")
                
                # Show sync reminder if data is old
                if True:  # Mock condition for old data
                    st.warning("⚠️ **Sync Reminder:** No new files detected in 4 days. Please ensure your latest financial data is uploaded to SharePoint.")
                
            else:
                st.info("🔌 SharePoint folder not connected. Click 'Connect SharePoint' to set up automatic synchronization.")
        
        with col2:
            if st.session_state.get("sharepoint_connected", False):
                if st.button("🔄 Sync Now", help="Manually trigger SharePoint synchronization"):
                    with st.spinner("Synchronizing with SharePoint..."):
                        # Simulate sync process
                        import time
                        time.sleep(2)
                        
                        # Mock new files found
                        st.session_state["sharepoint_files"] = [
                            {"name": "July_2025_Payroll.xlsx", "modified": "2025-07-31", "size": "45 KB", "type": "Payroll"},
                            {"name": "Q3_2025_Expenses.csv", "modified": "2025-07-30", "size": "23 KB", "type": "Expenses"},
                            {"name": "Revenue_Report_July.xlsx", "modified": "2025-07-29", "size": "67 KB", "type": "Revenue"}
                        ]
                        
                        st.success("✅ SharePoint sync completed! Found 3 new files.")
                        st.session_state["sharepoint_last_sync"] = "2025-08-01 " + "12:00"
                        st.rerun()
                
                if st.button("⚙️ Settings", help="Configure SharePoint sync settings"):
                    st.info("SharePoint sync settings would open in a modal")
                    
            else:
                if st.button("🔗 Connect SharePoint", type="primary", help="Set up SharePoint folder synchronization"):
                    with st.spinner("Connecting to SharePoint..."):
                        # Simulate connection process
                        import time
                        time.sleep(2)
                        st.session_state["sharepoint_connected"] = True
                        st.session_state["sharepoint_folder"] = "/Financial Data/Monthly Reports"
                        st.success("✅ SharePoint connected successfully!")
                        st.rerun()

        # Display SharePoint files if available
        if st.session_state.get("sharepoint_files"):
            st.markdown("**📋 Files from SharePoint:**")
            
            # Create expandable file list
            with st.expander(f"📁 SharePoint Files ({len(st.session_state['sharepoint_files'])} files found)", expanded=True):
                for i, file in enumerate(st.session_state["sharepoint_files"]):
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        
                        with col1:
                            st.write(f"📄 **{file['name']}**")
                        with col2:
                            st.caption(f"Modified: {file['modified']}")
                        with col3:
                            st.caption(f"Size: {file['size']}")
                        with col4:
                            if st.button("📊 Analyze", key=f"analyze_sp_{i}", help=f"Analyze {file['name']}"):
                                # Mock data based on file type
                                if file['type'] == 'Payroll':
                                    mock_data = pd.DataFrame({
                                        "Employee": ["John Doe", "Jane Smith", "Mike Johnson", "Sarah Wilson"],
                                        "Salary": [5200, 4800, 5500, 4600],
                                        "Bonuses": [520, 480, 550, 460]
                                    })
                                elif file['type'] == 'Expenses':
                                    mock_data = pd.DataFrame({
                                        "Category": ["Travel", "Office Supplies", "Utilities", "Software"],
                                        "Amount": [1500, 850, 650, 1200]
                                    })
                                else:  # Revenue
                                    mock_data = pd.DataFrame({
                                        "Month": ["May", "June", "July"],
                                        "Revenue": [15000, 18000, 16500]
                                    })
                                
                                st.session_state["current_data"] = mock_data
                                st.session_state["current_file"] = file['name']
                                
                                with st.spinner(f"Analyzing {file['name']}..."):
                                    insights = generate_insights(mock_data, file['type'])
                                    st.session_state["last_insights"] = insights
                                    st.session_state["last_file_source"] = f"SharePoint: {file['name']}"
                                
                                st.success(f"✅ Analysis completed for {file['name']}")
                                st.rerun()
                        
                        st.divider()

        # SharePoint sync configuration
        if st.session_state.get("sharepoint_connected", False):
            st.markdown("---")
            with st.expander("🔧 SharePoint Sync Configuration"):
                st.markdown("**Automatic Sync Settings:**")
                
                col1, col2 = st.columns(2)
                with col1:
                    sync_frequency = st.selectbox(
                        "Sync Frequency:",
                        ["Hourly", "Daily", "Weekly", "Manual only"],
                        index=1
                    )
                    
                    reminder_threshold = st.number_input(
                        "Send reminder after (days without new data):",
                        min_value=1,
                        max_value=30,
                        value=3
                    )
                
                with col2:
                    file_types = st.multiselect(
                        "File types to sync:",
                        ["Excel (.xlsx)", "CSV (.csv)", "PDF (.pdf)"],
                        default=["Excel (.xlsx)", "CSV (.csv)"]
                    )
                    
                    notification_email = st.text_input(
                        "Notification email:",
                        value=st.session_state.get("username", "") + "@example.com"
                    )
                
                if st.button("💾 Save Sync Settings"):
                    st.success("✅ SharePoint sync settings saved successfully!")
                    st.info(f"📧 You'll receive reminders at {notification_email} if no new data is detected for {reminder_threshold} days.")

        st.markdown("---")

        # Manual file upload section
        st.markdown("**📤 Manual File Upload:**")
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
            st.session_state["current_data"] = df
            st.session_state["current_file"] = uploaded_file.name

            if st.button("Generate Insights from Upload"):
                with st.spinner("Analyzing uploaded file..."):
                    insights = generate_insights(df, None)  # Pass None instead of insight_option
                    st.session_state["last_insights"] = insights
                    st.session_state["last_file_source"] = f"Manual Upload: {uploaded_file.name}"

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
            st.markdown("---")
            st.subheader("🤖 AI-Generated Insights")
            
            # Show data source
            if "last_file_source" in st.session_state:
                st.caption(f"📁 Data source: {st.session_state['last_file_source']}")
            
            # Display insights
            for section in st.session_state["last_insights"].split("\n"):
                if section.strip():
                    # Display raw section using st.text to avoid Markdown processing
                    st.text(section.strip())

            if "last_model_used" in st.session_state:
                st.caption(f"🤖 Model used: {st.session_state['last_model_used']}")

            # Show data preview if available
            if "current_data" in st.session_state:
                with st.expander("📊 View Data Preview"):
                    st.dataframe(st.session_state["current_data"].head(10))
                
                # Display chart
                display_chart(st.session_state["current_data"])

            # Sync options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📤 Sync to Xero"):
                    st.success("✅ Data has been synced to Xero. A copy of the data has been forwarded to Affintive's internal system.")
            
            with col2:
                if st.session_state.get("sharepoint_connected", False):
                    if st.button("📁 Save to SharePoint"):
                        st.success("✅ Analysis results saved to your SharePoint folder for future reference.")

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

            # Primary staff analysis button (Client Summary - main action per DOA)
            if st.button("📋 Generate Client Summary", type="primary", help="Quick client profile for meeting preparation"):
                with st.spinner("Generating comprehensive client summary..."):
                    # Generate client summary using the new function
                    summary = generate_client_summary(
                        client_data.get('business_name', ''),
                        client_data.get('contact_person', ''),
                        client_data.get('industry', ''),
                        client_data.get('annual_revenue', 0),
                        client_data.get('num_employees', 0),
                        client_data.get('key_challenges', '')
                    )
                    
                    st.subheader("📊 Client Summary Report") 
                    # Display the summary with proper formatting
                    for section in summary.split("\n"):
                        if section.strip():
                            st.text(section.strip())

                    st.success("✅ Client summary generated - ready for meeting preparation!")

            # Secondary analysis button (Deep Analysis - secondary action per DOA)
            st.markdown("---")
            if st.button("🔍 Deep Pain Point Analysis", help="Detailed onboarding analysis for comprehensive planning"):
                with st.spinner("Analyzing client data for detailed insights..."):
                    # Generate actual AI insights based on the provided data
                    insights = generate_onboarding_insights(
                        client_data.get('business_name', ''),
                        client_data.get('contact_person', ''),
                        client_data.get('industry', ''),
                        client_data.get('annual_revenue', 0),
                        client_data.get('num_employees', 0),
                        client_data.get('key_challenges', '')
                    )
                    
                    st.subheader("🎯 Detailed Pain Point Analysis")
                    # Display the insights with proper formatting
                    for section in insights.split("\n"):
                        if section.strip():
                            st.text(section.strip())

                    st.info("⚠️ **Staff Reminder:** This detailed analysis is for comprehensive strategic planning and due diligence.")

        else:
            st.info("👆 Please submit client information above to proceed with staff analysis")

        st.markdown("---")
        st.caption("💡 This prototype demonstrates the client-to-staff workflow. Document collection can be handled separately in the full implementation.")

    # --- CLIENT SUMMARY PAGE ---
    def client_summary():
        st.subheader("📋 Client Summary Dashboard")
        st.caption("Quick reference client profile for staff preparation")

        # Client selection dropdown
        st.markdown("**Select Client:**")
        client_options = [
            "TechStart Solutions Pty Ltd",
            "Digital Dynamics Inc", 
            "Growth Partners LLC",
            "Innovation Labs Co",
            "Future Finance Group"
        ]
        
        selected_client = st.selectbox("Choose client to view summary", client_options)
        
        # Mock client data based on selection
        client_profiles = {
            "TechStart Solutions Pty Ltd": {
                "business_name": "TechStart Solutions Pty Ltd",
                "contact_person": "Sarah Johnson",
                "industry": "Software Development & IT Services",
                "annual_revenue": 850000.00,
                "num_employees": 12,
                "key_challenges": "Cash flow management during project cycles, scaling team efficiently, managing client expectations and project timelines, need better financial forecasting tools"
            },
            "Digital Dynamics Inc": {
                "business_name": "Digital Dynamics Inc",
                "contact_person": "Michael Chen",
                "industry": "Digital Marketing & E-commerce",
                "annual_revenue": 1250000.00,
                "num_employees": 18,
                "key_challenges": "Rapid growth scaling issues, need for better financial controls, client acquisition cost optimization, team productivity improvement"
            },
            "Growth Partners LLC": {
                "business_name": "Growth Partners LLC",
                "contact_person": "Amanda Rodriguez",
                "industry": "Business Consulting & Strategy",
                "annual_revenue": 2100000.00,
                "num_employees": 25,
                "key_challenges": "Complex project portfolio management, need for advanced analytics, client reporting automation, operational efficiency improvements"
            },
            "Innovation Labs Co": {
                "business_name": "Innovation Labs Co", 
                "contact_person": "David Kim",
                "industry": "Technology R&D & Product Development",
                "annual_revenue": 680000.00,
                "num_employees": 8,
                "key_challenges": "R&D budget allocation optimization, project ROI tracking, intellectual property management, funding preparation"
            },
            "Future Finance Group": {
                "business_name": "Future Finance Group",
                "contact_person": "Lisa Thompson",
                "industry": "Financial Services & Fintech",
                "annual_revenue": 3200000.00,
                "num_employees": 35,
                "key_challenges": "Regulatory compliance management, digital transformation initiatives, risk management optimization, customer onboarding automation"
            }
        }
        
        # Get selected client data
        client_data = client_profiles[selected_client]
        
        # Display client data summary in a compact format with fixed industry display
        st.markdown("**Client Overview:**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Annual Revenue", f"${client_data['annual_revenue']:,.0f}")
        with col2:
            st.metric("Employees", f"{client_data['num_employees']}")
        with col3:
            st.markdown("**Industry:**")
            st.caption(client_data['industry'])
        
        st.markdown(f"**Contact:** {client_data['contact_person']}")
        
        # Main summary generation button (primary action)
        if st.button("📋 Generate Client Summary", type="primary", help="Quick one-page summary for meeting preparation"):
            with st.spinner("Generating comprehensive client summary..."):
                # Generate actual AI summary based on the selected client data
                summary = generate_client_summary(
                    client_data.get('business_name', ''),
                    client_data.get('contact_person', ''),
                    client_data.get('industry', ''),
                    client_data.get('annual_revenue', 0),
                    client_data.get('num_employees', 0),
                    client_data.get('key_challenges', '')
                )
                
                st.subheader("📊 Client Summary Report")
                # Display the summary with proper formatting
                for section in summary.split("\n"):
                    if section.strip():
                        st.text(section.strip())

                st.success("✅ Client summary generated successfully!")
                st.info("💡 **Usage:** This summary is optimized for quick reference before client meetings, calls, or strategic planning sessions.")
        
        # Secondary action - Deep analysis (existing functionality) 
        st.markdown("---")
        if st.button("🔍 Deep Pain Point Analysis", help="Detailed onboarding analysis (DYN-10)"):
            with st.spinner("Generating detailed pain point analysis..."):
                # Use existing detailed analysis function
                insights = generate_onboarding_insights(
                    client_data.get('business_name', ''),
                    client_data.get('contact_person', ''),
                    client_data.get('industry', ''),
                    client_data.get('annual_revenue', 0),
                    client_data.get('num_employees', 0),
                    client_data.get('key_challenges', '')
                )
                
                st.subheader("🎯 Detailed Pain Point Analysis")
                # Display the insights with proper formatting
                for section in insights.split("\n"):
                    if section.strip():
                        st.text(section.strip())

                st.info("⚠️ **Staff Reminder:** This is a detailed analysis for comprehensive client onboarding and strategic planning.")
        
        st.markdown("---")
        st.caption("💡 **Quick Summary** is the main tool for meeting prep. **Deep Analysis** provides comprehensive insights for strategic planning.")

    # --- ALERTS WORKFLOW PAGE ---
    def alerts_workflow():
        st.subheader("🔔 Smart Alerts Workflow")
        st.caption("Automated follow-ups and task scheduling for account managers")

        # Create tabs for different sections
        tab1, tab2, tab3 = st.tabs(["📅 Create New Alert", "📋 Active Alerts", "📊 Alert Analytics"])

        with tab1:
            st.markdown("**Schedule New Alert:**")
            
            # Client selection
            client_options = [
                "TechStart Solutions Pty Ltd",
                "Digital Dynamics Inc",
                "Growth Partners LLC",
                "Innovation Labs Co",
                "Future Finance Group"
            ]
            selected_client = st.selectbox("Select Client", client_options)
            
            # Purpose/Task selection
            st.markdown("**Alert Purpose:**")
            purpose = st.radio(
                "Choose task type:",
                ["Monthly Closure", "Outstanding Items Follow-up", "Customer Satisfaction Survey", "SharePoint Data Sync Reminder"],
                help="Select the type of automated alert to schedule"
            )
            
            # Scheduling options
            st.markdown("**Scheduling Options:**")
            schedule_type = st.radio(
                "Schedule Type:",
                ["One-time", "Recurring"],
                horizontal=True
            )
            
            if schedule_type == "One-time":
                col1, col2 = st.columns(2)
                with col1:
                    alert_date = st.date_input("Alert Date")
                with col2:
                    alert_time = st.time_input("Alert Time")
            else:
                frequency = st.selectbox(
                    "Frequency:",
                    ["Daily", "Weekly", "Monthly", "Quarterly"]
                )
                if frequency == "Weekly":
                    day_of_week = st.selectbox(
                        "Day of Week:",
                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    )
                elif frequency == "Monthly":
                    day_of_month = st.number_input(
                        "Day of Month:", 
                        min_value=1, 
                        max_value=28, 
                        value=1
                    )
            
            # Additional details
            st.markdown("**Alert Details:**")
            custom_message = st.text_area(
                "Custom Message (optional):",
                placeholder="Add any specific instructions or notes for this alert..."
            )
            
            # Priority level
            priority = st.select_slider(
                "Priority Level:",
                options=["Low", "Medium", "High", "Critical"],
                value="Medium"
            )
            
            # Create alert button
            if st.button("🔔 Schedule Alert", type="primary"):
                # Store alert in session state (in real app, this would go to database)
                if "alerts" not in st.session_state:
                    st.session_state["alerts"] = []
                
                new_alert = {
                    "client": selected_client,
                    "purpose": purpose,
                    "schedule_type": schedule_type,
                    "date": str(alert_date) if schedule_type == "One-time" else None,
                    "time": str(alert_time) if schedule_type == "One-time" else None,
                    "frequency": frequency if schedule_type == "Recurring" else None,
                    "custom_message": custom_message,
                    "priority": priority,
                    "status": "Active",
                    "created_date": "2025-08-01"  # Mock current date
                }
                
                st.session_state["alerts"].append(new_alert)
                st.success(f"✅ Alert scheduled successfully for {selected_client}!")
                st.info(f"📋 **Alert Summary:** {purpose} - {schedule_type} - Priority: {priority}")

        with tab2:
            st.markdown("**Active Alerts Overview:**")
            
            # Mock some default alerts if none exist
            if "alerts" not in st.session_state or len(st.session_state["alerts"]) == 0:
                st.session_state["alerts"] = [
                    {
                        "client": "TechStart Solutions Pty Ltd",
                        "purpose": "Monthly Closure",
                        "schedule_type": "Recurring",
                        "frequency": "Monthly",
                        "priority": "High",
                        "status": "Active",
                        "created_date": "2025-07-15",
                        "next_trigger": "2025-08-15"
                    },
                    {
                        "client": "Digital Dynamics Inc",
                        "purpose": "Outstanding Items Follow-up",
                        "schedule_type": "Recurring",
                        "frequency": "Weekly",
                        "priority": "Medium",
                        "status": "Active",
                        "created_date": "2025-07-20",
                        "next_trigger": "2025-08-05"
                    },
                    {
                        "client": "Growth Partners LLC",
                        "purpose": "SharePoint Data Sync Reminder",
                        "schedule_type": "Recurring",
                        "frequency": "Weekly",
                        "priority": "Medium",
                        "status": "Active",
                        "created_date": "2025-07-25",
                        "next_trigger": "2025-08-02"
                    },
                    {
                        "client": "TechStart Solutions Pty Ltd",
                        "purpose": "Customer Satisfaction Survey",
                        "schedule_type": "One-time",
                        "date": "2025-08-10",
                        "priority": "Low",
                        "status": "Pending",
                        "created_date": "2025-08-01"
                    }
                ]
            
            # Display alerts in a table format
            if st.session_state["alerts"]:
                for i, alert in enumerate(st.session_state["alerts"]):
                    with st.expander(f"🔔 {alert['client']} - {alert['purpose']} ({alert['priority']} Priority)"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Client:** {alert['client']}")
                            st.write(f"**Task:** {alert['purpose']}")
                            st.write(f"**Type:** {alert['schedule_type']}")
                        
                        with col2:
                            if alert['schedule_type'] == 'Recurring':
                                st.write(f"**Frequency:** {alert.get('frequency', 'N/A')}")
                                st.write(f"**Next Trigger:** {alert.get('next_trigger', 'N/A')}")
                            else:
                                st.write(f"**Date:** {alert.get('date', 'N/A')}")
                                st.write(f"**Time:** {alert.get('time', 'N/A')}")
                            st.write(f"**Status:** {alert['status']}")
                        
                        with col3:
                            if st.button("✏️ Edit", key=f"edit_{i}"):
                                st.info("Edit functionality would open in a modal")
                            if st.button("🗑️ Delete", key=f"delete_{i}"):
                                st.session_state["alerts"].pop(i)
                                st.rerun()
            else:
                st.info("No active alerts. Create your first alert in the 'Create New Alert' tab.")

        with tab3:
            st.markdown("**Alert Analytics & Performance:**")
            
            # Mock analytics data
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Alerts", "15", "+6")
            with col2:
                st.metric("Active Alerts", "11", "+4")
            with col3:
                st.metric("Completed This Month", "28", "+12")
            with col4:
                st.metric("Success Rate", "96%", "+4%")
            
            st.markdown("**Recent Alert Activity:**")
            
            # Mock recent activity
            recent_activity = [
                {"date": "2025-08-01 09:00", "client": "TechStart Solutions", "action": "Monthly Closure Alert Triggered", "status": "✅ Completed"},
                {"date": "2025-08-01 08:30", "client": "Digital Dynamics", "action": "Outstanding Items Follow-up", "status": "📧 Email Sent"},
                {"date": "2025-08-01 08:00", "client": "Growth Partners", "action": "SharePoint Sync Reminder Sent", "status": "📧 Email Sent"},
                {"date": "2025-07-31 16:00", "client": "Innovation Labs", "action": "SharePoint Data Upload Reminder", "status": "⏳ Pending"},
                {"date": "2025-07-31 14:15", "client": "TechStart Solutions", "action": "Monthly Closure Reminder", "status": "✅ Completed"},
            ]
            
            for activity in recent_activity:
                with st.container():
                    col1, col2, col3 = st.columns([2, 3, 2])
                    with col1:
                        st.text(activity["date"])
                    with col2:
                        st.text(f"{activity['client']}: {activity['action']}")
                    with col3:
                        st.text(activity["status"])
                    st.divider()
            
            # Time savings calculation
            st.markdown("**⏰ Time Savings Analysis:**")
            col1, col2 = st.columns(2)
            with col1:
                st.info("**Manual Process:** ~45 minutes per follow-up")
            with col2:
                st.success("**Automated Process:** ~5 minutes per follow-up")
            
            st.metric("Estimated Monthly Time Saved", "16 hours", "+4 hours")

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
        
    elif page == "🔔 Alerts Workflow":
        alerts_workflow()

    elif page == "📋 Client Summary":
        client_summary()
