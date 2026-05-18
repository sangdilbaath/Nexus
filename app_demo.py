import streamlit as st
from google import genai
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import time
import datetime
import re
import concurrent.futures
from streamlit_mic_recorder import speech_to_text

# ============================================================
# SECTION 1: PAGE CONFIG & GLOBAL CSS
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
    --text-muted:    #adb5bd;
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

/* ── Title / Hero ── */
.hero-zone {
    padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.hero-title {
    font-family: var(--font-mono);
    font-size: 2rem;
    color: var(--accent);
    letter-spacing: -1px;
    margin: 0;
}
.hero-sub {
    color: var(--text-muted);
    font-size: 0.875rem;
    margin-top: 0.3rem;
}

/* ── Metric Cards ── */
.metric-row { display: flex; gap: 1rem; margin: 1rem 0; flex-wrap: wrap; }
.metric-card {
    background: var(--bg-card);
    border-radius: 10px;
    padding: 1rem 1.4rem;
    flex: 1;
    min-width: 140px;
    border-left: 3px solid var(--accent);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 20px #00d4aa18; }
.metric-card .label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-body); }
.metric-card .value { font-size: 1.6rem; font-family: var(--font-mono); color: var(--accent); font-weight: 700; }
.metric-card .value .unit { font-size: 0.9rem; font-weight: 400; color: var(--text-muted); margin-left: 3px; }
.metric-card .sub { font-size: 0.72rem; color: var(--text-muted); margin-top: 0.1rem; }

/* ── Buttons (secondary/generic) ── */
[data-testid="baseButton-secondary"], .stButton > button {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="baseButton-secondary"]:hover, .stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
[data-testid="baseButton-secondary"]:active, .stButton > button:active {
    transform: scale(0.97) !important;
}

/* ── Execute CTA Button (accent reserved here only) ── */
.cta-btn > button {
    background: linear-gradient(135deg, #00d4aa, #0099ff) !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    box-shadow: 0 4px 20px #00d4aa40 !important;
    transition: all 0.15s ease !important;
}
.cta-btn > button:hover { box-shadow: 0 6px 30px #00d4aa60 !important; transform: translateY(-1px) !important; }
.cta-btn > button:active { transform: scale(0.97) !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-size: 0.875rem !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px #00d4aa20 !important;
}
/* Focus visible for accessibility */
*:focus-visible { outline: 2px solid var(--accent) !important; outline-offset: 2px !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; border: 1px solid var(--border); overflow: hidden; }

/* ── Info / Warning / Error boxes ── */
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Sidebar branding ── */
.sidebar-brand {
    text-align: center;
    padding: 1rem 0 1.5rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.sidebar-brand .logo { font-family: var(--font-mono); font-size: 1.5rem; color: var(--accent); font-weight: 700; letter-spacing: 2px; }
.sidebar-brand .tagline { font-size: 0.72rem; color: var(--text-muted); letter-spacing: 1px; text-transform: uppercase; }

/* ── Section headers with accent bar ── */
.section-label {
    font-family: var(--font-body);
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
    padding-left: 8px;
    border-left: 3px solid var(--accent);
}

/* ── Audit trail ── */
.audit-item {
    background: var(--bg-card);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.4rem;
    font-size: 0.875rem;
    color: var(--text-muted);
    border-left: 2px solid var(--border);
}
.audit-item .audit-cmd { color: var(--text-primary); font-size: 0.875rem; margin-bottom: 2px; }
.audit-item .audit-meta { font-size: 0.72rem; color: var(--text-muted); display: flex; gap: 0.5rem; align-items: center; }
.audit-badge-ok  { background: #3fb95022; color: var(--success); border-radius: 4px; padding: 1px 6px; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
.audit-badge-err { background: #f8514922; color: var(--danger);  border-radius: 4px; padding: 1px 6px; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: #1c2333 !important;
    color: var(--success) !important;
    border: 1px solid var(--success) !important;
    border-radius: 8px !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
}

/* ── Status widget ── */
[data-testid="stStatusWidget"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}

/* ── Column pills ── */
.col-pills-wrap {
    max-height: 64px;
    overflow: hidden;
    margin: 0.5rem 0 1rem 0;
    transition: max-height 0.3s ease;
}
.col-pills-wrap.expanded { max-height: 400px; }
.col-pill {
    display: inline-block;
    background: var(--bg-card);
    color: var(--text-muted);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.15rem 0.6rem;
    font-size: 0.72rem;
    font-family: var(--font-mono);
    margin: 0.15rem;
}

/* ── Results panel ── */
.results-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-top: 1rem;
}

/* ── Chart gallery ── */
.chart-gallery-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
}
.chart-gallery-label {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-family: var(--font-mono);
    margin-bottom: 0.5rem;
}

/* ── Voice recording feedback ── */
.recording-indicator {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.8rem;
    color: var(--danger);
    margin-top: 0.3rem;
}
@keyframes pulse {
    0%   { opacity: 1; }
    50%  { opacity: 0.3; }
    100% { opacity: 1; }
}
.pulse-dot {
    width: 8px; height: 8px;
    background: var(--danger);
    border-radius: 50%;
    animation: pulse 1.2s infinite;
    display: inline-block;
}

/* ── Rate limit warning ── */
.rate-limit-badge {
    font-size: 0.72rem;
    color: var(--warning);
    font-family: var(--font-mono);
    text-align: right;
    margin-top: 0.3rem;
}

/* ── Responsive ── */
@media (max-width: 900px) {
    .metric-row { flex-wrap: wrap; }
    .metric-card { min-width: 120px; }
    .hero-title { font-size: 1.4rem; }
}
@media (max-width: 480px) {
    .metric-card .value { font-size: clamp(1rem, 4vw, 1.6rem); }
}

/* ── Page load animation ── */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
.hero-zone    { animation: fadeUp 0.3s ease both; }
.metric-row   { animation: fadeUp 0.4s ease 0.1s both; }
.section-label{ animation: fadeUp 0.4s ease 0.15s both; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SECTION 2: CONSTANTS
# ============================================================
MAX_FILE_SIZE_MB = 10
MAX_REQUESTS_PER_SESSION = 50
AI_TIMEOUT_SECONDS = 30
PYTHON_KEYWORDS = {'import', 'def', 'df', 'plt', 'pd', 'for', 'if', 'print', 'return', '=', 'fig', 'ax'}

# ============================================================
# SECTION 3: SESSION STATE
# ============================================================
for key, default in {
    "query_text":       "",
    "updated_df":       None,
    "chart_gallery":    [],     # list of {label, img_bytes, timestamp}
    "command_history":  [],     # list of {cmd, ts, ok, rows_before, rows_after}
    "df":               None,
    "last_filename":    None,
    "show_all_data":    False,
    "show_all_cols":    False,
    "request_count":    0,
    "is_recording":     False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ============================================================
# SECTION 4: HELPERS
# ============================================================
def clean_ai_code(raw: str) -> str:
    """Strip all markdown code fences from AI-generated Python."""
    raw = re.sub(r"```(?:python)?", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```", "", raw)
    return raw.strip()

def is_likely_python(code: str) -> bool:
    """Reject responses that are explanations, not code."""
    return any(kw in code for kw in PYTHON_KEYWORDS)

def sanitize_col_name(name: str) -> str:
    """Escape column names for safe inclusion in prompts."""
    return re.sub(r"[^\w\s\-\.]", "_", str(name))

def get_df_summary(df: pd.DataFrame) -> str:
    """Richer schema: dtypes + nulls + value stats."""
    lines = []
    for col in df.columns:
        safe_col = sanitize_col_name(col)
        dtype    = str(df[col].dtype)
        nulls    = int(df[col].isnull().sum())
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            stats = f"min={desc['min']:.2f}, max={desc['max']:.2f}, mean={desc['mean']:.2f}"
        else:
            top5 = df[col].dropna().astype(str).value_counts().head(5).index.tolist()
            stats = "top values: " + ", ".join(top5)
        lines.append(f"- `{safe_col}` ({dtype}, {nulls} nulls) → {stats}")
    return "\n".join(lines)

def render_metrics(df: pd.DataFrame):
    num_cols    = df.select_dtypes(include='number').shape[1]
    missing_pct = round(df.isnull().mean().mean() * 100, 1)
    mem_kb      = round(df.memory_usage(deep=True).sum() / 1024, 1)
    mem_unit    = "KB" if mem_kb < 1024 else "MB"
    mem_val     = mem_kb if mem_kb < 1024 else round(mem_kb / 1024, 2)
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
                <div class="value">{missing_pct}<span class="unit">%</span></div>
                <div class="sub">null values</div>
            </div>
            <div class="metric-card">
                <div class="label">Memory</div>
                <div class="value">{mem_val}<span class="unit">{mem_unit}</span></div>
                <div class="sub">in use</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def load_file(uploaded_file) -> pd.DataFrame:
    """Load CSV (with encoding fallback) or Excel (with merged-cell detection)."""
    name = uploaded_file.name
    if name.endswith('.csv'):
        raw = uploaded_file.read()
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                df = pd.read_csv(io.BytesIO(raw), encoding=enc, parse_dates=True)
                break
            except (UnicodeDecodeError, Exception):
                continue
        else:
            raise ValueError("Could not decode CSV with utf-8, latin-1, or cp1252.")
    else:
        df = pd.read_excel(uploaded_file, parse_dates=True)
        unnamed = [c for c in df.columns if str(c).startswith("Unnamed")]
        if len(unnamed) > df.shape[1] * 0.3:
            st.warning(
                "⚠️ **Merged-cell headers detected.** Many columns read as 'Unnamed'. "
                "Consider un-merging header rows in Excel before uploading.",
                icon="⚠️"
            )

    # Auto-parse object columns that look like dates
    for col in df.select_dtypes(include='object').columns:
        try:
            converted = pd.to_datetime(df[col], infer_datetime_format=True, errors='coerce')
            if converted.notna().sum() / max(len(df), 1) > 0.7:
                df[col] = converted
        except Exception:
            pass

    return df

def call_gemini_with_timeout(client, prompt: str, timeout: int = AI_TIMEOUT_SECONDS) -> str:
    """Call Gemini API with a hard timeout."""
    def _call():
        return client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        ).text

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_call)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise TimeoutError(f"Gemini API did not respond within {timeout}s.")

def trim_memory():
    """Keep command history bounded; trim chart gallery to last 10."""
    if len(st.session_state.command_history) > 50:
        st.session_state.command_history = st.session_state.command_history[-50:]
    if len(st.session_state.chart_gallery) > 10:
        st.session_state.chart_gallery = st.session_state.chart_gallery[-10:]

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

    st.markdown('<div class="section-label">Session Controls</div>', unsafe_allow_html=True)
    if st.button("🗑️ Reset Session", use_container_width=True):
        for key in ["updated_df", "chart_gallery", "query_text",
                    "command_history", "df", "last_filename",
                    "show_all_data", "show_all_cols", "request_count"]:
            st.session_state[key] = (
                [] if key in ("command_history", "chart_gallery") else
                ""  if key in ("query_text",) else
                0   if key == "request_count" else
                False if key in ("show_all_data", "show_all_cols") else
                None
            )
        st.rerun()

    # ── Audit trail ──
    if st.session_state.command_history:
        st.markdown('<div class="section-label">Audit Trail</div>', unsafe_allow_html=True)
        with st.expander(f"📝 {len(st.session_state.command_history)} Command(s)", expanded=False):
            for entry in reversed(st.session_state.command_history):
                badge = f'<span class="audit-badge-ok">✓ OK</span>' if entry["ok"] \
                        else f'<span class="audit-badge-err">✗ Fail</span>'
                rows_info = ""
                if entry.get("rows_before") is not None and entry.get("rows_after") is not None:
                    rows_info = f'· {entry["rows_before"]:,} → {entry["rows_after"]:,} rows'
                st.markdown(f"""
                    <div class="audit-item">
                        <div class="audit-cmd">{entry["cmd"]}</div>
                        <div class="audit-meta">{badge}<span>{entry["ts"]}</span><span>{rows_info}</span></div>
                    </div>
                """, unsafe_allow_html=True)

    # ── Rate limit indicator ──
    remaining = MAX_REQUESTS_PER_SESSION - st.session_state.request_count
    st.markdown(f'<div class="rate-limit-badge">◈ {remaining}/{MAX_REQUESTS_PER_SESSION} requests left</div>',
                unsafe_allow_html=True)

    st.divider()
    st.markdown("""
        <div style="background:#1c2333; border:1px solid #30363d; border-radius:8px; padding:0.7rem 1rem; text-align:center;">
            <div style="font-size:0.72rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Nexus v3.1 · 2026 Pro</div>
        </div>
    """, unsafe_allow_html=True)

# ============================================================
# SECTION 6: HERO & MAIN CONTENT
# ============================================================
st.markdown("""
    <div class="hero-zone">
        <div class="hero-title">◈ NEXUS Excel AI</div>
        <div class="hero-sub">Professional Spreadsheet Intelligence Engine</div>
    </div>
""", unsafe_allow_html=True)

if not api_key:
    st.markdown("""
        <div style="background:#1c2333; border:1px solid #30363d; border-radius:12px;
                    padding:2rem; text-align:center; margin-top:2rem;">
            <div style="font-size:2.5rem; margin-bottom:0.5rem;">🔑</div>
            <div style="font-family:'Space Mono',monospace; color:#e6edf3; font-size:1rem;">API Key Required</div>
            <div style="color:#adb5bd; font-size:0.875rem; margin-top:0.4rem;">
                Enter your Gemini API Key in the sidebar to activate the engine.
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

try:
    client = genai.Client(api_key=api_key)

    # ── File Upload ──
    st.markdown('<div class="section-label">Data Source</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload spreadsheet", type=["xlsx", "csv"],
        label_visibility="collapsed",
        help="Supported: .csv and .xlsx · Max 10 MB"
    )

    if uploaded_file is None:
        st.markdown("""
            <div style="background:#1c2333; border:2px dashed #30363d; border-radius:12px;
                        padding:3rem; text-align:center; margin-top:1rem;">
                <div style="font-size:2.5rem;">📂</div>
                <div style="font-family:'Space Mono',monospace; color:#8b949e; margin-top:0.5rem;">
                    Drop a CSV or XLSX file above to get started
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.stop()

    # ── File size guard ──
    if uploaded_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(
            f"❌ File too large ({round(uploaded_file.size/1024/1024, 1)} MB). "
            f"Maximum allowed is {MAX_FILE_SIZE_MB} MB.",
            icon="🚫"
        )
        st.stop()

    # ── Load file on change ──
    if uploaded_file.name != st.session_state.last_filename:
        with st.spinner("Loading file..."):
            st.session_state.df               = load_file(uploaded_file)
            st.session_state.last_filename    = uploaded_file.name
            st.session_state.updated_df       = None
            st.session_state.chart_gallery    = []
            st.session_state.command_history  = []
            st.session_state.request_count    = 0

    current_df = (st.session_state.updated_df
                  if st.session_state.updated_df is not None
                  else st.session_state.df)

    # ── Dataset Overview ──
    st.markdown('<div class="section-label">Dataset Overview</div>', unsafe_allow_html=True)
    render_metrics(current_df)

    # ── Column Pills ──
    pills_html = "".join([f'<span class="col-pill">{sanitize_col_name(c)}</span>'
                          for c in current_df.columns])
    wrap_cls = "col-pills-wrap" + (" expanded" if st.session_state.show_all_cols else "")
    st.markdown(f'<div class="{wrap_cls}">{pills_html}</div>', unsafe_allow_html=True)
    if st.button("▾ Show all columns" if not st.session_state.show_all_cols else "▴ Collapse columns",
                 key="toggle_cols"):
        st.session_state.show_all_cols = not st.session_state.show_all_cols
        st.rerun()

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
            st.session_state.is_recording = False
        # Visual feedback when recording
        if st.session_state.get("is_recording"):
            st.markdown('<div class="recording-indicator"><span class="pulse-dot"></span> Listening...</div>',
                        unsafe_allow_html=True)

    with col_txt:
        final_query = st.text_area(
            "command_input",
            value=st.session_state.query_text,
            placeholder="e.g., 'Bar chart of Sales by Region' or 'Add a profit margin column'",
            label_visibility="collapsed",
            height=80,
        )

    # Rate limit check
    if st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
        st.warning(f"⚠️ Session limit of {MAX_REQUESTS_PER_SESSION} requests reached. Reset the session to continue.")
    else:
        col_exec, _ = st.columns([2, 5])
        with col_exec:
            st.markdown('<div class="cta-btn">', unsafe_allow_html=True)
            execute_btn = st.button("▶  Execute Command", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if execute_btn and final_query.strip():
            df_summary   = get_df_summary(current_df)
            rows_before  = len(current_df)

            prompt = f"""You are a senior Python Data Analyst. The user has a Pandas DataFrame named 'df'.

DATAFRAME SCHEMA (column · dtype · nulls · value ranges):
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
4. CHART STYLE: Dark theme is already applied via plt.style.use('dark_background').
   Use accent '#00d4aa' for main data series.
5. Do NOT import libraries — df, plt, pd, and buf are already available.
"""

            last_error    = None
            clean_code    = ""
            exec_success  = False

            with st.status("⚡ Nexus Engine Running...", expanded=True) as status:
                for attempt in range(2):
                    try:
                        if attempt == 0:
                            st.write("📡 Connecting to Gemini...")
                        else:
                            st.write(f"🔁 Retrying with error context...")

                        retry_prompt = prompt if attempt == 0 else (
                            prompt + f"\n\nYour previous attempt failed with:\n`{last_error}`\nFix the code."
                        )

                        raw_response = call_gemini_with_timeout(client, retry_prompt)

                        st.write("🧬 Parsing generated code...")
                        clean_code = clean_ai_code(raw_response)

                        if not is_likely_python(clean_code):
                            raise ValueError(
                                "AI returned an explanation instead of code. "
                                f"Preview: {clean_code[:120]}"
                            )

                        buf       = io.BytesIO()
                        local_ctx = {
                            'df':  current_df.copy(),
                            'plt': plt,
                            'pd':  pd,
                            'buf': buf,
                        }

                        # Apply dark theme automatically before exec
                        plt.style.use('dark_background')

                        st.write("🚀 Executing analysis...")
                        exec(compile(clean_code, "<nexus_ai>", "exec"), {}, local_ctx)

                        result_df = local_ctx.get('df')
                        if isinstance(result_df, pd.DataFrame):
                            st.session_state.updated_df = result_df

                        if local_ctx['buf'].tell() > 0:
                            local_ctx['buf'].seek(0)
                            img_bytes = local_ctx['buf'].getvalue()
                            st.session_state.chart_gallery.append({
                                "label":     final_query[:60],
                                "img_bytes": img_bytes,
                                "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                            })
                        
                        exec_success = True
                        break

                    except Exception as e:
                        last_error = str(e)
                        if attempt == 1:
                            status.update(label="❌ Execution Failed", state="error", expanded=True)
                            st.error(f"**Error:** `{last_error}`")
                            st.code(clean_code or "No code generated.", language="python")

            rows_after = (len(st.session_state.updated_df)
                          if st.session_state.updated_df is not None else rows_before)

            st.session_state.command_history.append({
                "cmd":         final_query,
                "ts":          datetime.datetime.now().strftime("%H:%M:%S"),
                "ok":          exec_success,
                "rows_before": rows_before,
                "rows_after":  rows_after,
            })
            st.session_state.request_count += 1
            st.session_state.query_text    = ""
            trim_memory()

            if exec_success:
                result_df = (st.session_state.updated_df
                             if st.session_state.updated_df is not None else current_df)
                row_diff = rows_after - rows_before
                diff_str = (f"+{row_diff:,}" if row_diff >= 0 else f"{row_diff:,}") + " rows"
                status.update(label=f"✅ Done — {diff_str}", state="complete", expanded=False)
                time.sleep(0.4)
                st.rerun()

    # ── Results Panel ──
    has_chart  = bool(st.session_state.chart_gallery)
    has_table  = st.session_state.updated_df is not None

    if has_table or has_chart:
        st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)
        st.markdown('<div class="results-panel">', unsafe_allow_html=True)

        if has_table and has_chart:
            col_table, col_chart = st.columns([1, 1], gap="large")
        elif has_chart:
            col_chart = st.container(); col_table = None
        else:
            col_table = st.container(); col_chart = None

        if col_table and has_table:
            with col_table:
                st.markdown("**Updated Table**")
                st.dataframe(st.session_state.updated_df.head(15), use_container_width=True)

        if col_chart and has_chart:
            with col_chart:
                latest = st.session_state.chart_gallery[-1]
                st.markdown("**Latest Chart**")
                st.image(latest["img_bytes"], use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── Chart Gallery ──
        if len(st.session_state.chart_gallery) > 1:
            st.markdown('<div class="section-label">Chart Gallery</div>', unsafe_allow_html=True)
            for entry in reversed(st.session_state.chart_gallery[:-1]):
                st.markdown(f'<div class="chart-gallery-item"><div class="chart-gallery-label">◈ {entry["label"]} · {entry["timestamp"]}</div>', unsafe_allow_html=True)
                st.image(entry["img_bytes"], use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # ── Downloads ──
        if has_table:
            st.markdown('<div class="section-label">Export</div>', unsafe_allow_html=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                st.session_state.updated_df.to_excel(writer, index=False)

            dl1, dl2, _ = st.columns([1, 1, 3])
            with dl1:
                st.download_button(
                    "📥 Download Excel",
                    data=output.getvalue(),
                    file_name="nexus_output.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with dl2:
                st.download_button(
                    "📥 Download CSV",
                    data=st.session_state.updated_df.to_csv(index=False).encode('utf-8'),
                    file_name="nexus_output.csv",
                    mime="text/csv",
                    use_container_width=True
                )

except Exception as e:
    st.error(f"**Initialization Error:** {e}")
    st.caption("Check your Gemini API Key in the sidebar.")
