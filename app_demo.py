import streamlit as st
from google import genai
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import uuid
import os
import time
from streamlit_mic_recorder import speech_to_text

# ============================================================
# SECTION 1: HARDWARE ACTIVATION
# ============================================================
def get_current_machine_id():
    return hex(uuid.getnode())

def is_activated():
    current_id = get_current_machine_id()
    # NOTE: Move this to an env variable or config file — never hardcode IDs in source
    master_id = os.environ.get("NEXUS_MASTER_ID", "0x58cdc9382aec")
    if current_id == master_id:
        return True
    license_path = "license.nexus"
    if os.path.exists(license_path):
        with open(license_path, "r") as f:
            stored_id = f.read().strip()
            return current_id == stored_id
    return False

# Security Gate
if not is_activated():
    st.set_page_config(page_title="Nexus Activation", page_icon="🔐")
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        body, [data-testid="stAppViewContainer"] { background: #0a0a0f; color: #e0e0e0; font-family: 'JetBrains Mono', monospace; }
        .block-container { padding-top: 4rem; }
        </style>
    """, unsafe_allow_html=True)
    st.error("🚫 NEXUS AI — PRODUCT NOT ACTIVATED")
    st.code(f"Machine ID: {get_current_machine_id()}", language="bash")
    st.caption("Contact your administrator with the Machine ID above.")
    st.stop()

# ============================================================
# SECTION 2: PAGE CONFIG & GLOBAL CSS
# ============================================================
st.set_page_config(
    page_title="Nexus Excel AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root Variables ── */
:root {
    --bg-primary:    #0d1117;
    --bg-secondary:  #161b22;
    --bg-card:       #1c2333;
    --border:        #30363d;
    --accent:        #00d4aa;
    --accent-dim:    #00d4aa22;
    --accent-hover:  #00ffcc;
    --text-primary:  #e6edf3;
    --text-muted:    #8b949e;
    --danger:        #f85149;
    --warning:       #e3b341;
    --success:       #3fb950;
    --font-mono:     'Space Mono', monospace;
    --font-body:     'DM Sans', sans-serif;
}

/* ── Global Reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}
[data-testid="stSidebar"] { background-color: var(--bg-secondary) !important; border-right: 1px solid var(--border); }
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
.block-container { padding: 2rem 2.5rem 2rem 2.5rem !important; max-width: 1400px; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Title ── */
h1 { font-family: var(--font-mono) !important; color: var(--accent) !important; letter-spacing: -1px; }
h2, h3, h4 { font-family: var(--font-mono) !important; color: var(--text-primary) !important; }

/* ── Metric Cards ── */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
.metric-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.4rem; flex: 1; min-width: 140px;
    border-left: 3px solid var(--accent);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px #00d4aa18; }
.metric-card .label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
.metric-card .value { font-size: 1.6rem; font-family: var(--font-mono); color: var(--accent); font-weight: 700; }
.metric-card .sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.1rem; }

/* ── Buttons ── */
[data-testid="baseButton-secondary"], .stButton > button {
    background: var(--bg-card) !important; color: var(--accent) !important;
    border: 1px solid var(--accent) !important; border-radius: 8px !important;
    font-family: var(--font-mono) !important; font-size: 0.82rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="baseButton-secondary"]:hover, .stButton > button:hover {
    background: var(--accent-dim) !important; box-shadow: 0 0 12px #00d4aa40 !important;
}
[data-testid="baseButton-primary"] > button {
    background: var(--accent) !important; color: #0d1117 !important;
    border: none !important; font-weight: 700 !important;
}

/* ── Execute CTA Button ── */
.cta-btn > button {
    background: linear-gradient(135deg, #00d4aa, #0099ff) !important;
    color: #0d1117 !important; font-weight: 700 !important;
    font-size: 0.95rem !important; border: none !important;
    border-radius: 10px !important; padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 20px #00d4aa40 !important;
}
.cta-btn > button:hover { box-shadow: 0 6px 30px #00d4aa60 !important; transform: translateY(-1px) !important; }

/* ── Inputs ── */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: var(--bg-card) !important; color: var(--text-primary) !important;
    border: 1px solid var(--border) !important; border-radius: 8px !important;
    font-family: var(--font-body) !important;
}
.stTextInput > div > div > input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 2px #00d4aa20 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid var(--border); overflow: hidden; }

/* ── Info / Warning / Error boxes ── */
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Sidebar branding ── */
.sidebar-brand {
    text-align: center; padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid var(--border); margin-bottom: 1rem;
}
.sidebar-brand .logo { font-family: var(--font-mono); font-size: 1.5rem; color: var(--accent); font-weight: 700; letter-spacing: 2px; }
.sidebar-brand .tagline { font-size: 0.7rem; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }

/* ── Section headers ── */
.section-label {
    font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.5rem;
    padding-bottom: 0.3rem; border-bottom: 1px solid var(--border);
}

/* ── Audit trail ── */
.audit-item {
    background: var(--bg-card); border-radius: 6px; padding: 0.4rem 0.7rem;
    margin-bottom: 0.3rem; font-size: 0.78rem; color: var(--text-muted);
    border-left: 2px solid var(--accent);
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #1c2333 !important; color: var(--success) !important;
    border: 1px solid var(--success) !important; border-radius: 8px !important;
    font-family: var(--font-mono) !important; font-weight: 700 !important;
}

/* ── Login page ── */
.login-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 16px; padding: 2.5rem; text-align: center;
    box-shadow: 0 8px 40px #00000060; max-width: 400px; margin: 0 auto;
}
.login-logo { font-family: var(--font-mono); font-size: 2.5rem; color: var(--accent); letter-spacing: 4px; }
.login-sub { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 2rem; }

/* ── Status widget ── */
[data-testid="stStatusWidget"] { background: var(--bg-card) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }

/* ── Column list pills ── */
.col-pill {
    display: inline-block; background: var(--accent-dim); color: var(--accent);
    border: 1px solid var(--accent); border-radius: 20px; padding: 0.15rem 0.6rem;
    font-size: 0.72rem; font-family: var(--font-mono); margin: 0.15rem;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SECTION 3: PASSWORD AUTHENTICATION
# ============================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("""
            <div class="login-card">
                <div class="login-logo">NEXUS</div>
                <div class="login-sub">Enterprise Data Intelligence Platform</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # NOTE: Move password to env var — never hardcode in source
        user_pwd = st.text_input("Master Password", type="password", placeholder="Enter your password...")
        
        if st.button("Authenticate →", use_container_width=True):
            correct_password = os.environ.get("NEXUS_PASSWORD", "samr3113")
            if user_pwd == correct_password:
                st.session_state.logged_in = True
                st.toast("Authentication Successful ✅")
                time.sleep(0.4)
                st.rerun()
            else:
                st.error("❌ Access Denied — Incorrect Password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color: #8b949e; font-size:0.7rem;">Nexus v3.0 · 2026 Pro Edition</p>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# SECTION 4: SESSION STATE INITIALIZATION
# ============================================================
for key, default in {
    "query_text": "",
    "updated_df": None,
    "last_chart": None,
    "command_history": [],
    "df": None,
    "last_filename": None,
    "show_all_data": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# SECTION 5: SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="logo">◈ NEXUS</div>
            <div class="tagline">Excel AI · Pro Edition</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">API Configuration</div>', unsafe_allow_html=True)
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIza...")

    st.divider()

    st.markdown('<div class="section-label">Session Controls</div>', unsafe_allow_html=True)
    if st.button("🗑️ Reset Session", use_container_width=True):
        for key in ["updated_df", "last_chart", "query_text", "command_history", "df", "last_filename", "show_all_data"]:
            st.session_state[key] = [] if key == "command_history" else None if key not in ["query_text", "show_all_data"] else ("" if key == "query_text" else False)
        st.rerun()

    if st.session_state.command_history:
        st.divider()
        st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
        with st.expander(f"📝 {len(st.session_state.command_history)} Command(s)", expanded=False):
            for i, cmd in enumerate(reversed(st.session_state.command_history), 1):
                st.markdown(f'<div class="audit-item">#{len(st.session_state.command_history)-i+1} {cmd}</div>', unsafe_allow_html=True)

    st.divider()
    machine_id = get_current_machine_id()
    st.markdown(f"""
        <div style="background:#1c2333; border:1px solid #30363d; border-radius:8px; padding:0.7rem 1rem;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Licensed Device</div>
            <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#00d4aa; margin-top:0.2rem;">{machine_id[:18]}...</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 6: HELPERS
# ============================================================
def clean_ai_code(raw: str) -> str:
    """Strip all markdown code fences from AI-generated Python."""
    lines = raw.strip().splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()

def get_df_summary(df: pd.DataFrame) -> str:
    dtype_map = df.dtypes.apply(lambda x: str(x)).to_dict()
    nulls = df.isnull().sum().to_dict()
    summary_lines = [f"- {col} ({dtype_map[col]}, {nulls[col]} nulls)" for col in df.columns]
    return "\n".join(summary_lines)

def render_metrics(df: pd.DataFrame):
    num_cols = df.select_dtypes(include='number').shape[1]
    missing_pct = round(df.isnull().mean().mean() * 100, 1)
    mem_kb = round(df.memory_usage(deep=True).sum() / 1024, 1)
    st.markdown(f"""
        <div class="metric-row">
            <div class="metric-card">
                <div class="label">Rows</div>
                <div class="value">{df.shape[0]:,}</div>
                <div class="sub">records</div>
            </div>
            <div class="metric-card">
                <div class="label">Columns</div>
                <div class="value">{df.shape[1]}</div>
                <div class="sub">{num_cols} numeric</div>
            </div>
            <div class="metric-card">
                <div class="label">Missing</div>
                <div class="value">{missing_pct}%</div>
                <div class="sub">null values</div>
            </div>
            <div class="metric-card">
                <div class="label">Memory</div>
                <div class="value">{mem_kb}</div>
                <div class="sub">KB in use</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 7: MAIN APP
# ============================================================
st.markdown("# ◈ NEXUS Excel AI")
st.markdown('<p style="color:#8b949e; margin-top:-0.8rem; font-size:0.85rem;">Professional Spreadsheet Intelligence Engine</p>', unsafe_allow_html=True)

if not api_key:
    st.markdown("""
        <div style="background:#1c2333; border:1px solid #30363d; border-radius:12px; padding:2rem; text-align:center; margin-top:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔑</div>
            <div style="font-family:'Space Mono',monospace; color:#e6edf3; font-size:1rem;">API Key Required</div>
            <div style="color:#8b949e; font-size:0.85rem; margin-top:0.4rem;">Enter your Gemini API Key in the sidebar to activate the engine.</div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    client = genai.Client(api_key=api_key)

    # ── File Upload ──
    st.markdown('<div class="section-label" style="margin-top:1.5rem;">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload spreadsheet", type=["xlsx", "csv"],
        label_visibility="collapsed",
        help="Supported formats: .csv and .xlsx"
    )

    if uploaded_file is None:
        st.markdown("""
            <div style="background:#1c2333; border:2px dashed #30363d; border-radius:12px; padding:3rem; text-align:center; margin-top:1rem;">
                <div style="font-size:2.5rem;">📂</div>
                <div style="font-family:'Space Mono',monospace; color:#8b949e; margin-top:0.5rem;">Drop a CSV or XLSX file above to get started</div>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Reset df if a new file is uploaded
    if uploaded_file.name != st.session_state.last_filename:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.last_filename = uploaded_file.name
        st.session_state.updated_df = None
        st.session_state.last_chart = None
        st.session_state.command_history = []

    current_df = st.session_state.updated_df if st.session_state.updated_df is not None else st.session_state.df

    # ── Data Overview ──
    st.divider()
    st.markdown('<div class="section-label">Dataset Overview</div>', unsafe_allow_html=True)
    render_metrics(current_df)

    # ── Column Pills ──
    pills_html = "".join([f'<span class="col-pill">{c}</span>' for c in current_df.columns])
    st.markdown(f'<div style="margin:0.5rem 0 1rem 0;">{pills_html}</div>', unsafe_allow_html=True)

    # ── Data Preview ──
    col_title, col_toggle = st.columns([5, 1])
    with col_title:
        st.markdown('<div class="section-label">Data Preview</div>', unsafe_allow_html=True)
    with col_toggle:
        if st.session_state.show_all_data:
            if st.button("🔼 Less", use_container_width=True):
                st.session_state.show_all_data = False; st.rerun()
        else:
            if st.button("🔽 More", use_container_width=True):
                st.session_state.show_all_data = True; st.rerun()

    preview_df = current_df if st.session_state.show_all_data else current_df.head(5)
    st.dataframe(preview_df, use_container_width=True, height=220)

    st.divider()

    # ── Command Interface ──
    st.markdown('<div class="section-label">Command Interface</div>', unsafe_allow_html=True)
    
    col_mic, col_txt = st.columns([1, 6])
    with col_mic:
        text_from_voice = speech_to_text(
            language='en-IN',
            start_prompt="🎙️",
            stop_prompt="🛑 Stop",
            just_once=True,
            key='nexus_stt'
        )
        if text_from_voice:
            st.session_state.query_text = text_from_voice

    with col_txt:
        final_query = st.text_input(
            "command_input",
            value=st.session_state.query_text,
            placeholder="e.g., 'Bar chart of Item_Name vs Sales_This_Month' or 'Add a profit margin column'",
            label_visibility="collapsed",
        )

    st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
    execute_btn = st.button("▶  Execute Command", use_container_width=False)
    st.markdown('</div>', unsafe_allow_html=True)

    if execute_btn and final_query.strip():
        df_summary = get_df_summary(current_df)
        
        prompt = f"""You are a senior Python Data Analyst. The user has a Pandas DataFrame named 'df'.

DATAFRAME SCHEMA:
{df_summary}

SAMPLE DATA (first 3 rows as JSON):
{current_df.head(3).to_json(orient='records', indent=2)}

USER TASK: {final_query}

STRICT RULES:
1. Return ONLY valid Python code. No markdown, no explanations, no backticks.
2. DATA TASKS: Modify 'df' in place (filter, add columns, sort, etc.).
3. CHART TASKS: Never overwrite 'df'. Use matplotlib. End EVERY chart with:
   plt.tight_layout()
   plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#1c2333')
   plt.close()
4. CHART STYLE: Use dark theme. Background '#1c2333', text '#e6edf3', accent '#00d4aa'.
   Example setup: plt.figure(figsize=(10,5)); ax = plt.gca()
   ax.set_facecolor('#0d1117'); plt.gcf().set_facecolor('#1c2333')
   ax.tick_params(colors='#8b949e'); ax.xaxis.label.set_color('#e6edf3')
5. Do NOT import libraries — df, plt, pd, and buf are already available.
"""

        with st.status("⚡ Nexus Engine Running...", expanded=True) as status:
            try:
                st.write("📡 Connecting to Gemini...")
                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt
                )

                st.write("🧬 Parsing generated code...")
                clean_code = clean_ai_code(response.text)

                buf = io.BytesIO()
                local_ctx = {
                    'df': current_df.copy(),
                    'plt': plt,
                    'pd': pd,
                    'buf': buf
                }

                st.write("🚀 Executing analysis...")
                exec(compile(clean_code, "<nexus_ai>", "exec"), {}, local_ctx)

                result_df = local_ctx.get('df')
                if isinstance(result_df, pd.DataFrame):
                    st.session_state.updated_df = result_df

                if local_ctx['buf'].tell() > 0:
                    local_ctx['buf'].seek(0)
                    st.session_state.last_chart = local_ctx['buf'].getvalue()
                else:
                    st.session_state.last_chart = None

                st.session_state.command_history.append(final_query)
                st.session_state.query_text = ""

                status.update(label="✅ Command Executed Successfully", state="complete", expanded=False)
                time.sleep(0.6)
                st.rerun()

            except Exception as e:
                status.update(label="❌ Execution Failed", state="error", expanded=True)
                st.error(f"**Error:** `{e}`")
                st.code(clean_code if 'clean_code' in locals() else "No code generated", language="python")

    # ── Results Display ──
    if st.session_state.updated_df is not None or st.session_state.last_chart:
        st.divider()
        st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)

        if st.session_state.last_chart and st.session_state.updated_df is not None:
            col_table, col_chart = st.columns([1, 1], gap="large")
        elif st.session_state.last_chart:
            col_chart = st.container()
            col_table = None
        else:
            col_table = st.container()
            col_chart = None

        if col_table and st.session_state.updated_df is not None:
            with col_table:
                st.markdown("**Updated Table**")
                st.dataframe(st.session_state.updated_df.head(15), use_container_width=True)

        if col_chart and st.session_state.last_chart:
            with col_chart:
                st.markdown("**Generated Chart**")
                st.image(st.session_state.last_chart, use_container_width=True)

        # ── Download ──
        if st.session_state.updated_df is not None:
            st.markdown("<br>", unsafe_allow_html=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.updated_df.to_excel(writer, index=False)

            dl_col1, dl_col2, _ = st.columns([1, 1, 3])
            with dl_col1:
                st.download_button(
                    label="📥 Download Excel",
                    data=output.getvalue(),
                    file_name="nexus_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with dl_col2:
                csv_out = st.session_state.updated_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_out,
                    file_name="nexus_output.csv",
                    mime="text/csv",
                    use_container_width=True
                )

except Exception as e:
    st.error(f"**Initialization Error:** {e}")
    st.caption("Check your Gemini API Key in the sidebar.")
