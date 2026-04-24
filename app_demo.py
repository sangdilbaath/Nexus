import streamlit as st
from google import genai
import pandas as pd

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Nexus AI", page_icon="🚀", layout="centered")

# --- 2. AI CONFIGURATION ---
# IMPORTANT: For public deployment, use st.secrets["GEMINI_API_KEY"] instead of hardcoding!
API_KEY = "AIzaSyB2KlDX_ROJ-Cb4G7xrLJtAXuZ85ibo-ho"
client = genai.Client(api_key=API_KEY)

# --- 3. SESSION STATE (MEMORY) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "show_full_data" not in st.session_state:
    st.session_state.show_full_data = False
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

# --- 4. HEADER ---
st.title("🚀 Nexus AI")
st.caption("Enterprise Cloud Edition")

# --- 5. FILE UPLOAD LOGIC ---
uploaded_file = st.file_uploader("Upload your Database (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Only read the file if it is a new upload
    if st.session_state.df is None or st.session_state.last_uploaded != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)
            
            st.session_state.last_uploaded = uploaded_file.name
            st.success(f"📁 Loaded '{uploaded_file.name}' | {len(st.session_state.df)} rows found.")
            st.session_state.messages.append({"role": "assistant", "content": f"I have successfully loaded the dataset `{uploaded_file.name}`. How would you like to analyze or modify it?"})
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# --- 6. EXCEL PREVIEW & "SHOW MORE" LOGIC ---
if st.session_state.df is not None:
    st.subheader("📊 Live Data Preview")
    
    # Display the dataframe based on the toggle state
    if st.session_state.show_full_data:
        st.dataframe(st.session_state.df, use_container_width=True)
    else:
        st.dataframe(st.session_state.df.head(5), use_container_width=True)
        
    # The Toggle Button
    button_label = "Show Less" if st.session_state.show_full_data else "Show More"
    if st.button(button_label):
        st.session_state.show_full_data = not st.session_state.show_full_data
        st.rerun() 

st.divider()

# --- 7. CHAT HISTORY UI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. THE ENTERPRISE BRAIN ---
if prompt := st.chat_input("Command Nexus..."):
    # Show user message instantly
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        try:
            # If we have data, use the strict Code Sandbox
            if st.session_state.df is not None:
                message_placeholder.markdown("⚙️ *Analyzing dataset and executing logic...*")
                
                system_prompt = f"""
                You are a Python Data Analyst. The user has a Pandas DataFrame named 'df'.
                Current Columns: {list(st.session_state.df.columns)}
                
                User Request: {prompt}
                
                CRITICAL RULES:
                1. Return ONLY valid Python code. No markdown formatting, no backticks, no explanations.
                2. Modify 'df' directly in place, or reassign it to 'df'.
                3. Do NOT include 'print' statements.
                """
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite", 
                    contents=system_prompt
                )
                
                # Clean the AI's code output
                clean_code = response.text.strip()
                if clean_code.startswith("```"):
                    clean_code = clean_code.split("\n", 1)[-1]
                if clean_code.endswith("```"):
                    clean_code = clean_code.rsplit("\n", 1)[0]
                clean_code = clean_code.strip()
                
                # Safely execute the code on our session state dataframe
                local_context = {'df': st.session_state.df.copy(), 'pd': pd}
                exec(clean_code, {}, local_context)
                
                # Save the modified data back into Streamlit's memory
                st.session_state.df = local_context['df']
                reply = "Command executed successfully. I have updated the data table above."
                
                # Save message and refresh the whole app to show the new table
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun() 
                
            # If no data is uploaded, just chat normally
            else:
                message_placeholder.markdown("✨ *Thinking...*")
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite", 
                    contents=prompt
                )
                reply = response.text
                message_placeholder.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
        except Exception as e:
            error_msg = f"System Error: Could not execute command. Make sure the logic is mathematically possible for this dataset. \n\n*Error details: {e}*"
            message_placeholder.markdown(f"❌ {error_msg}")
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
