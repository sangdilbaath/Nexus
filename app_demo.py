import streamlit as st
from google import genai
from google.genai import types
import pandas as pd

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Nexus AI", page_icon="🚀", layout="centered")

# --- 2. API KEY CONFIGURATION (SECURE USER INPUT) ---
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Securely connect your AI brain.")
    user_api_key = st.text_input("Gemini API Key", type="password", placeholder="Paste your key here...")
    st.markdown("[Get your free API key here](https://aistudio.google.com/app/apikey)")
    st.divider()
    st.markdown("🔒 *Your key is never stored. It resets when you close the app.*")

# Stop the app completely if the user hasn't entered a key yet
if not user_api_key:
    st.title("🚀 Welcome to Nexus AI")
    st.warning("👈 Please open the sidebar menu and enter your Gemini API Key to unlock the app.")
    st.stop()

# Initialize the AI with the user's secure key
client = genai.Client(api_key=user_api_key)

# --- 3. SESSION STATE (MEMORY) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "df" not in st.session_state:
    st.session_state.df = None
if "show_full_data" not in st.session_state:
    st.session_state.show_full_data = False
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None 

# --- 4. HEADER ---
st.title("🚀 Nexus AI")
st.caption("Enterprise Cloud Edition")

# --- 5. FILE UPLOAD LOGIC ---
uploaded_file = st.file_uploader("Upload your Database (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    if st.session_state.df is None or st.session_state.last_uploaded != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)
            
            st.session_state.last_uploaded = uploaded_file.name
            welcome_msg = f"I have successfully loaded the dataset `{uploaded_file.name}`. How would you like to analyze it?"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# --- 6. EXCEL PREVIEW & "SHOW MORE" LOGIC ---
if st.session_state.df is not None:
    st.subheader("📊 Live Data Preview")
    
    if st.session_state.show_full_data:
        st.dataframe(st.session_state.df, use_container_width=True)
    else:
        st.dataframe(st.session_state.df.head(5), use_container_width=True)
        
    button_label = "Show Less" if st.session_state.show_full_data else "Show More"
    if st.button(button_label):
        st.session_state.show_full_data = not st.session_state.show_full_data
        st.rerun() 

st.divider()

# --- 7. CHAT HISTORY UI ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 8. THE ENTERPRISE BRAIN (PROCESS LOGIC) ---
def process_command(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            if st.session_state.df is not None:
                message_placeholder.markdown("⚙️ *Analyzing dataset and executing logic...*")
                system_prompt = f"""
                You are a Python Data Analyst. The user has a Pandas DataFrame named 'df'.
                Current Columns: {list(st.session_state.df.columns)}
                Task: {user_text}
                CRITICAL RULES:
                1. Return ONLY valid Python code. No markdown formatting, no backticks, no explanations.
                2. Modify 'df' directly in place.
                """
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=system_prompt)
                
                clean_code = response.text.strip().replace("```python", "").replace("```", "").strip()
                
                local_context = {'df': st.session_state.df.copy(), 'pd': pd}
                exec(clean_code, {}, local_context)
                
                st.session_state.df = local_context['df']
                reply = "Command executed successfully. I have updated the data table."
            else:
                message_placeholder.markdown("✨ *Thinking...*")
                response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=user_text)
                reply = response.text
                
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
            
        except Exception as e:
            error_msg = f"System Error: Logic failed. ({e})"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

# --- 9. DUAL INPUT: KEYBOARD OR VOICE ---
st.caption("🗣️ Speak to Nexus or type below:")
col1, col2 = st.columns([1, 5])

with col1:
    audio_value = st.audio_input("Record", label_visibility="collapsed")

with col2:
    text_prompt = st.chat_input("Command Nexus...")

# Process Voice Input
if audio_value and audio_value != st.session_state.last_audio:
    st.session_state.last_audio = audio_value  
    with st.spinner("Nexus is translating audio..."):
        try:
            audio_part = types.Part
