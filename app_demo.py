import streamlit as st
from google import genai
import pandas as pd
import matplotlib.pyplot as plt
import io
import uuid
import os
from streamlit_mic_recorder import speech_to_text


# --- 2. PAGE CONFIG ---
st.set_page_config(page_title="Nexus Excel AI", page_icon="📊", layout="wide")
# --- LAYER 1: PASSWORD AUTHENTICATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Create a centered login box using columns
    st.write("<br><br><br>", unsafe_allow_html=True) # Adds some top spacing
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 Nexus Enterprise Login</h2>", unsafe_allow_html=True)
        st.write("Please enter your master password to access the engine.")
        
        # The password input box
        user_pwd = st.text_input("Master Password", type="password")
        
        if st.button("Access System", use_container_width=True):
            # YOUR SECRET PASSWORD GOES HERE
            if user_pwd == "demo123": 
                st.session_state.logged_in = True
                st.toast('Authentication Successful!', icon='✅')
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Access Denied: Incorrect Password")
    
    # This is the magic wall! It stops the rest of the app from running.
    st.stop() 
# ----------------------------------------
# Initialize Session States
if "query_text" not in st.session_state:
    st.session_state.query_text = ""
if "updated_df" not in st.session_state:
    st.session_state.updated_df = None
if "last_chart" not in st.session_state:
    st.session_state.last_chart = None

st.title("🚀 Nexus: Professional Excel AI")

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    
    st.divider()
    if st.button("🗑️ Reset All Data"):
        st.session_state.updated_df = None
        st.session_state.last_chart = None
        st.session_state.query_text = ""
        st.rerun()
    
    st.info(f"Authorized Device")
    st.write("Nexus v3.1 | 2026 Pro Edition")

# --- 4. MAIN APP LOGIC ---
if api_key:
    try:
        client = genai.Client(api_key=api_key)
        uploaded_file = st.file_uploader("Upload your spreadsheet", type=["xlsx", "csv"])

        if uploaded_file:
            if "df" not in st.session_state:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.df = pd.read_csv(uploaded_file)
                else:
                    st.session_state.df = pd.read_excel(uploaded_file)
            
            current_df = st.session_state.updated_df if st.session_state.updated_df is not None else st.session_state.df

            st.write("### 📄 Data Preview:", current_df.head(5))
            st.divider()

            # --- GEMINI-STYLE VOICE & TEXT INPUT ---
            st.write("### 💬 Command Nexus")
            
            col_mic, col_txt = st.columns([1, 5])
            
            with col_mic:
                # Browser-native speech recognition (The 'Gemini' way)
                # This populates st.session_state.query_text automatically
                text_from_voice = speech_to_text(
                    language='en-IN',
                    start_prompt="🎙️ Speak",
                    stop_prompt="🛑 Stop",
                    just_once=True,
                    key='nexus_stt'
                )
                
                if text_from_voice:
                    st.session_state.query_text = text_from_voice

            with col_txt:
                # The text box uses the session state as its value
                final_query = st.text_input(
                    "Command Box (Speak or Type):", 
                    value=st.session_state.query_text,
                    placeholder="e.g., 'Calculate total profit for each row'"
                )

            if st.button("▶️ Execute Command") and final_query:
                # Logic for Gemini to process the command
                prompt = f"""
                You are a Python Data Analyst. The user has a Pandas DataFrame named 'df'.
                Columns: {list(current_df.columns)}
                Task: {final_query}
                
                CRITICAL RULES:
                1. Return ONLY valid Python code. No markdown formatting or explanations.
                2. Modify 'df' directly.
                3. IF creating a chart/graph:
                   - DO NOT use plt.show().
                   - You must save the chart to the provided buffer.
                   - End your chart code exactly like this:
                     plt.savefig(buf, format='png', bbox_inches='tight')
                     plt.close()
                """

                with st.spinner("Nexus is processing..."):
                    try:
                        response = client.models.generate_content(
                            model="gemini-2.5-flash-lite", 
                            contents=prompt
                        )
                        
                        # --- UPGRADED CODE CLEANER ---
                        clean_code = response.text.strip()
                        if clean_code.startswith("```"):
                            clean_code = clean_code.split("\n", 1)[-1]
                        if clean_code.endswith("```"):
                            clean_code = clean_code.rsplit("\n", 1)[0]
                        clean_code = clean_code.strip()
                        # -----------------------------

                        buf = io.BytesIO()
                        local_context = {'df': current_df.copy(), 'plt': plt, 'pd': pd, 'buf': buf}
                        
                        exec(clean_code, {}, local_context)
                        
                        st.session_state.updated_df = local_context['df']
                        if buf.tell() > 0:
                            buf.seek(0)
                            st.session_state.last_chart = buf.getvalue()
                        else:
                            st.session_state.last_chart = None
                        
                        # Success! Clear the command box for next time
                        st.session_state.query_text = ""
                        st.rerun()

                    except Exception as e:
                        st.error(f"Execution Error: {e}")
            # --- 5. RESULTS DISPLAY ---
            if st.session_state.updated_df is not None:
                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### ✅ Updated Table")
                    st.dataframe(st.session_state.updated_df.head(10))
                with c2:
                    if st.session_state.last_chart:
                        st.image(st.session_state.last_chart)

                # DOWNLOAD
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.updated_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Download Result",
                    data=output.getvalue(),
                    file_name="nexus_output.xlsx"
                )

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("👈 Please enter your API Key in the sidebar.")
