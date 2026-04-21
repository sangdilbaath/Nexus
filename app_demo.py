import streamlit as st
from google import genai
import pandas as pd
import matplotlib.pyplot as plt
import io
import time
from streamlit_mic_recorder import speech_to_text

# ==========================================
# MODULE 1: SECURITY & AUTHENTICATION
# ==========================================
def check_security():
    """A safer, password-based security system instead of hardware IDs."""
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False

    if not st.session_state.is_authenticated:
        st.set_page_config(page_title="Nexus Login", page_icon="🔐")
        st.title("🔐 Nexus AI Security Gate")
        
        # In a real app, store this password securely in Streamlit Secrets!
        APP_PASSWORD = "demo123" 
        
        user_pwd = st.text_input("Enter Application Password:", type="password")
        if st.button("Unlock"):
            if user_pwd == APP_PASSWORD:
                st.session_state.is_authenticated = True
                st.rerun()
            else:
                st.error("🚫 Access Denied: Incorrect Password")
        st.stop() # Stops the rest of the app from loading until unlocked

# ==========================================
# MODULE 2: AI ENGINE & SAFE EXECUTION
# ==========================================
def run_ai_command(client, df, user_query):
    """Handles the AI logic and safely executes the code."""
    prompt = f"""
    You are a strict Data Analyst AI. You have a Pandas DataFrame named 'df'.
    Columns available: {list(df.columns)}
    User Request: "{user_query}"
    
    CRITICAL GUARDRAILS:
    1. If the user request is NOT about data analysis, charts, or modifying this dataset, you MUST reply with exactly: "ERROR: INVALID_REQUEST". Do not write code.
    2. Return ONLY valid Python code. No markdown formatting.
    3. Modify 'df' directly for data tasks. DO NOT overwrite 'df' when making charts.
    4. For charts, end exactly with:
       plt.savefig(buf, format='png', bbox_inches='tight')
       plt.close()
    """
    
    # 1. Ask the AI
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite", 
        contents=prompt
    )
    clean_code = response.text.strip()
    
    # Check if the AI triggered our guardrail
    if "ERROR: INVALID_REQUEST" in clean_code:
        raise ValueError("I am a data analysis assistant. I cannot help with requests outside of exploring your spreadsheet.")

    # Clean up markdown if the AI forgot the rules
    if clean_code.startswith("```"):
        clean_code = clean_code.split("\n", 1)[-1]
    if clean_code.endswith("```"):
        clean_code = clean_code.rsplit("\n", 1)[0]
    
    # 2. Setup a Sandboxed Environment for execution
    buf = io.BytesIO()
    # By setting __builtins__ to None, we stop the AI from running dangerous system commands
    safe_globals = {"__builtins__": {}} 
    local_context = {'df': df.copy(), 'plt': plt, 'pd': pd, 'buf': buf}
    
    # 3. Execute safely
    exec(clean_code, safe_globals, local_context)
    
    return local_context

# ==========================================
# MODULE 3: MAIN USER INTERFACE
# ==========================================
def main():
    # 1. Run Security Check First
    check_security()

    # 2. Setup Page & State
    st.set_page_config(page_title="Nexus Excel AI", page_icon="📊", layout="wide")
    st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

    if "query_text" not in st.session_state: st.session_state.query_text = ""
    if "updated_df" not in st.session_state: st.session_state.updated_df = None
    if "last_chart" not in st.session_state: st.session_state.last_chart = None
    if "command_history" not in st.session_state: st.session_state.command_history = []

    st.title("🚀 Nexus: Professional Excel AI")

    # 3. Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        # Best practice: Suggest using st.secrets for the API key in production
        api_key = st.text_input("Enter Gemini API Key", type="password", help="Get this from Google AI Studio")
        
        st.divider()
        if st.button("🗑️ Reset All Data"):
            for key in ["updated_df", "last_chart", "query_text", "command_history"]:
                st.session_state[key] = None if "df" in key or "chart" in key else ("" if "query" in key else [])
            st.rerun()
        
        if st.session_state.command_history:
            st.divider()
            with st.expander("📝 Session Audit Trail"):
                for i, cmd in enumerate(st.session_state.command_history, 1):
                    st.write(f"**{i}.** {cmd}")

    # 4. Core Application Logic
    if not api_key:
        st.info("👋 Welcome to Nexus. Please enter your Gemini API Key in the sidebar to start.")
        st.stop()

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error("Authentication Error: Invalid API Key.")
        st.stop()

    uploaded_file = st.file_uploader("Upload your spreadsheet (.csv or .xlsx)", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            if "df" not in st.session_state:
                if uploaded_file.name.endswith('.csv'):
                    st.session_state.df = pd.read_csv(uploaded_file)
                else:
                    st.session_state.df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error("Error reading file. Please ensure it is a valid CSV or Excel document.")
            st.stop()
        
        current_df = st.session_state.updated_df if st.session_state.updated_df is not None else st.session_state.df

        # Data Preview UI
        st.write("### 📄 Data Preview")
        st.dataframe(current_df.head(5), use_container_width=True)
        st.divider()

        # Input Area
        st.write("### 💬 Command Nexus")
        col_mic, col_txt = st.columns([1, 5])
        
        with col_mic:
            text_from_voice = speech_to_text(language='en-US', start_prompt="🎙️ Speak", stop_prompt="🛑 Stop", just_once=True, key='stt')
            if text_from_voice:
                st.session_state.query_text = text_from_voice

        with col_txt:
            final_query = st.text_input("Command Box:", value=st.session_state.query_text, placeholder="e.g., 'Make a bar chart of Sales'")

        # Execution Area
        if st.button("▶️ Execute Command") and final_query:
            with st.status("🧠 Nexus Engine Analyzing...", expanded=True) as status:
                try:
                    # Run our new, safe modular AI engine
                    st.write("Generating logic...")
                    result_context = run_ai_command(client, current_df, final_query)
                    
                    # Process Results
                    st.write("Rendering visuals...")
                    if isinstance(result_context.get('df'), pd.DataFrame):
                        st.session_state.updated_df = result_context['df']
                    
                    final_buf = result_context.get('buf')
                    if final_buf and final_buf.tell() > 0:
                        final_buf.seek(0)
                        st.session_state.last_chart = final_buf.getvalue()
                    else:
                        st.session_state.last_chart = None
                    
                    st.session_state.command_history.append(final_query)
                    st.session_state.query_text = ""
                    
                    status.update(label="Command Executed Successfully!", state="complete", expanded=False)
                    time.sleep(0.8)
                    st.rerun()

                # Specific Error Catching
                except ValueError as ve:
                    status.update(label="Request Rejected", state="error", expanded=False)
                    st.error(f"Guardrail Alert: {ve}")
                except SyntaxError:
                    status.update(label="Code Generation Error", state="error", expanded=False)
                    st.error("The AI generated invalid Python code. Please rephrase your request.")
                except Exception as e:
                    status.update(label="Execution Failed", state="error", expanded=False)
                    st.error(f"Unexpected Error: {e}")
        
        # Results Display
        if st.session_state.updated_df is not None or st.session_state.last_chart is not None:
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("#### ✅ Updated Table")
                st.dataframe(st.session_state.updated_df.head(10))
                
                # Download Button
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    st.session_state.updated_df.to_excel(writer, index=False)
                st.download_button("📥 Download Excel Result", data=output.getvalue(), file_name="nexus_output.xlsx")
            
            with c2:
                if st.session_state.last_chart:
                    st.write("#### 📊 Visualization")
                    st.image(st.session_state.last_chart)

# Run the application
if __name__ == "__main__":
    main()
