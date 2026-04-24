import streamlit as st
from google import genai
import pandas as pd
import speech_recognition as sr
from gtts import gTTS
import io

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Nexus AI", page_icon="🚀", layout="centered")

# --- 2. AI CONFIGURATION ---
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

# --- 4. VOICE ENGINE (TEXT-TO-SPEECH) ---
def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en')
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        # autoplay=True makes the AI speak instantly when the message loads!
        st.audio(audio_fp, format="audio/mp3", autoplay=True) 
    except Exception as e:
        st.warning(f"Voice engine skipped: {e}")

# --- 5. HEADER ---
st.title("🚀 Nexus AI")
st.caption("Enterprise Voice & Cloud Edition")

# --- 6. FILE UPLOAD LOGIC ---
uploaded_file = st.file_uploader("Upload your Database (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    if st.session_state.df is None or st.session_state.last_uploaded != uploaded_file.name:
        try:
            if uploaded_file.name.endswith('.csv'):
                st.session_state.df = pd.read_csv(uploaded_file)
            else:
                st.session_state.df = pd.read_excel(uploaded_file)
            
            st.session_state.last_uploaded = uploaded_file.name
            welcome_msg = f"I have successfully loaded the dataset {uploaded_file.name}. How would you like to analyze it?"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg, "speak": True})
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")

# --- 7. EXCEL PREVIEW & "SHOW MORE" LOGIC ---
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

# --- 8. CHAT HISTORY UI ---
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Only speak the very last message if it is flagged to speak
        if message.get("speak") and idx == len(st.session_state.messages) - 1:
            speak_text(message["content"])

# --- 9. THE ENTERPRISE BRAIN (PROCESS LOGIC) ---
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
                
            st.session_state.messages.append({"role": "assistant", "content": reply, "speak": True})
            st.rerun()
            
        except Exception as e:
            error_msg = f"System Error: Logic failed. ({e})"
            st.session_state.messages.append({"role": "assistant", "content": error_msg, "speak": True})
            st.rerun()

# --- 10. DUAL INPUT: KEYBOARD OR VOICE ---
st.caption("🗣️ Speak to Nexus or type below:")
col1, col2 = st.columns([1, 5])

with col1:
    # Native Streamlit Audio Input
    audio_value = st.audio_input("Record", label_visibility="collapsed")

with col2:
    # Standard Keyboard Input
    text_prompt = st.chat_input("Command Nexus...")

# Process Voice Input
if audio_value:
    with st.spinner("Translating audio..."):
        r = sr.Recognizer()
        with sr.AudioFile(audio_value) as source:
            audio_data = r.record(source)
            try:
                transcribed_text = r.recognize_google(audio_data)
                # Clear the audio widget by resetting it (optional, but good UX)
                process_command(transcribed_text)
            except sr.UnknownValueError:
                st.error("Could not understand audio. Please try again.")

# Process Keyboard Input
if text_prompt:
    process_command(text_prompt)
