import streamlit as st
import os
import time
import base64
from datetime import datetime
from dotenv import load_dotenv

# ─── Local modules ────────────────────────────────────────────────────────────
from config import DEFAULT_MODEL, MODEL_OPTIONS, EDGE_TTS_VOICE
from auth import (
    register_user, login_user, is_admin,
    list_histories, save_history, load_history_file, delete_history_file,
    make_title,
)
from admin import render_admin_dashboard
from ai_services import stream_ai, call_ai, call_stt
from tts_service import synthesize
from voice_component import voice_loop_component

load_dotenv()

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CRM Assistant",
    page_icon="",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

*, html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: #111118 !important; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbarActions"] { visibility: hidden; }

.block-container {
    max-width: 760px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
}

/* ── Auth card ── */
.auth-card {
    background: #1c1c2a;
    border: 1px solid #2a2a3e;
    border-radius: 20px;
    padding: 36px 32px;
    margin: 40px auto;
    max-width: 420px;
}
.auth-logo {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 20px rgba(124,58,237,.45);
    margin: 0 auto 18px;
}
.auth-title {
    color: #f1f5f9; font-size: 1.35rem; font-weight: 700;
    text-align: center; margin-bottom: 4px;
}
.auth-sub {
    color: #6b7280; font-size: 0.82rem;
    text-align: center; margin-bottom: 24px;
}
.auth-tab-row {
    display: flex; gap: 8px; margin-bottom: 20px;
}
.auth-tab {
    flex: 1; padding: 8px;
    border: 1px solid #2a2a3e; border-radius: 10px;
    color: #9ca3af; font-size: 0.83rem; font-weight: 500;
    text-align: center; cursor: pointer; background: #13131f;
    transition: all .2s;
}
.auth-tab.active {
    background: rgba(124,58,237,.18);
    border-color: #7c3aed; color: #c4b5fd;
}

/* ── Header ── */
.aria-header {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 0 16px;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 20px;
}
.aria-logo {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 16px rgba(124,58,237,.4);
    flex-shrink: 0;
}
.aria-name { font-size: 1rem; font-weight: 600; color: #f1f5f9; margin: 0; line-height: 1.3; }
.aria-status { font-size: 0.72rem; color: #6b7280; margin: 0; }
.dot-green {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%;
    margin-right: 4px; box-shadow: 0 0 5px #22c55e88;
}

/* ── Bubbles ── */
.msg-user { display: flex; justify-content: flex-end; margin: 8px 0; }
.msg-bot { display: flex; align-items: flex-end; gap: 8px; margin: 8px 0; }
.bubble-user {
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    color: #fff; padding: 10px 15px;
    border-radius: 18px 18px 4px 18px;
    max-width: 68%; font-size: 0.88rem; line-height: 1.6;
    white-space: pre-wrap; word-wrap: break-word;
    box-shadow: 0 4px 16px rgba(124,58,237,.3);
}
.bubble-bot {
    background: #1c1c2a; border: 1px solid #2a2a3e;
    color: #d1d5db; padding: 10px 15px;
    border-radius: 18px 18px 18px 4px;
    max-width: 68%; font-size: 0.88rem; line-height: 1.6;
    white-space: pre-wrap; word-wrap: break-word;
}
.bot-av {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, #7c3aed, #4f46e5);
    border-radius: 50%; display: flex;
    align-items: center; justify-content: center;
    font-size: 0.75rem; flex-shrink: 0;
}

/* ── Voice badge ── */
.voice-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(124,58,237,.15);
    border: 1px solid rgba(124,58,237,.35);
    color: #c4b5fd; border-radius: 20px;
    padding: 4px 12px; font-size: 0.78rem; font-weight: 500;
    margin-bottom: 14px;
}
.pulse {
    width: 8px; height: 8px; background: #a855f7;
    border-radius: 50%; animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity:1; transform:scale(1); }
    50% { opacity:.4; transform:scale(.75); }
}

/* ── Streaming indicator ── */
.streaming-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: #a855f7;
    border-radius: 50%;
    animation: blink 1s ease-in-out infinite;
    margin-left: 4px;
    vertical-align: middle;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.2; }
}

/* ── Input ── */
.stTextInput > div > div > input {
    background: #1c1c2a !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-size: 0.88rem !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,.2) !important;
}
.stTextInput > div > div > input::placeholder { color: #4b5563 !important; }

[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    color: #fff !important; border: none !important;
    border-radius: 12px !important; font-weight: 600 !important;
    font-size: 0.85rem !important; height: 42px !important;
    transition: all .2s !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(124,58,237,.45) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #0d0d14 !important; border-right: 1px solid #1e1e2e !important; }
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small { color: #9ca3af !important; }
[data-testid="stSidebar"] h3 {
    color: #6b7280 !important; font-size: 0.72rem !important;
    text-transform: uppercase !important; letter-spacing: 0.08em !important; font-weight: 600 !important;
}
.stButton > button {
    background: #1c1c2a !important; color: #d1d5db !important;
    border: 1px solid #2a2a3e !important; border-radius: 10px !important;
    font-size: 0.85rem !important;
}
.stButton > button:hover { border-color: #7c3aed !important; color: #fff !important; }
.stSelectbox > div > div {
    background: #1c1c2a !important; border: 1px solid #2a2a3e !important;
    border-radius: 10px !important; color: #d1d5db !important;
}
hr { border-color: #1e1e2e !important; }

.dl-box {
    background: rgba(124,58,237,.1); border: 1px solid rgba(124,58,237,.3);
    border-radius: 12px; padding: 12px 16px; margin: 12px 0;
    color: #c4b5fd; font-size: 0.84rem;
}

/* ── User chip in sidebar ── */
.user-chip {
    background: rgba(124,58,237,.12);
    border: 1px solid rgba(124,58,237,.3);
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
.user-chip-name { color: #f1f5f9; font-size: 0.85rem; font-weight: 600; }
.user-chip-co { color: #9ca3af; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
defaults = {
    "current_user": None,
    "messages": [],
    "model": DEFAULT_MODEL,
    "greeted": False,
    "voice_mode": False,
    "last_audio_id": None,
    "last_spoken_idx": -1,
    "session_id": None,
    "loaded_file": None,
    "auth_tab": "login",
    "voice_tts_b64": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "api_key" not in st.session_state:
    try:
        st.session_state.api_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
    except Exception:
        st.session_state.api_key = os.getenv("GROQ_API_KEY", "")

# ══════════════════════════════════════════════════════════════════════════════
# ─── AUTH SCREEN ──────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.current_user is None:

    st.markdown("""
    <div style="text-align:center;padding:30px 0 10px;">
      <div style="width:56px;height:56px;background:linear-gradient(135deg,#7c3aed,#4f46e5);
           border-radius:16px;display:inline-flex;align-items:center;justify-content:center;
           font-size:1.6rem;box-shadow:0 4px 24px rgba(124,58,237,.45);margin-bottom:14px;"></div>
      <div style="color:#f1f5f9;font-size:1.4rem;font-weight:700;margin-bottom:4px;">CRM Assistant</div>
      <div style="color:#6b7280;font-size:0.85rem;">Bigin & Zoho CRM Consultant</div>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_reg = st.tabs([" Login", " Register"])

    # ── Login Tab ─────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            co_in = st.text_input("Company Name", placeholder="e.g. Acme Pvt Ltd")
            pw_in = st.text_input("Password", type="password", placeholder="Your password")
            login_btn = st.form_submit_button("Login →", use_container_width=True)

        if login_btn:
            if not co_in.strip() or not pw_in.strip():
                st.error("Please fill in both fields.")
            else:
                ok, key_or_err, user = login_user(co_in, pw_in)
                if ok:
                    st.session_state.current_user = user
                    st.session_state.messages = []
                    st.session_state.greeted = False
                    st.session_state.last_spoken_idx = -1
                    st.session_state.last_audio_id = None
                    st.session_state.session_id = None
                    st.session_state.loaded_file = None
                    st.rerun()
                else:
                    st.error(key_or_err)

    # ── Register Tab ──────────────────────────────────────────────────────────
    with tab_reg:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        with st.form("register_form"):
            r_name = st.text_input("Your Name", placeholder="e.g. Rahul Sharma")
            r_co = st.text_input("Company Name", placeholder="e.g. Acme Pvt Ltd (used to log in)")
            r_phone = st.text_input("Phone Number", placeholder="e.g. 9876543210")
            r_pw = st.text_input("Create Password", type="password", placeholder="Min 6 characters")
            r_pw2 = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            reg_btn = st.form_submit_button("Create Account →", use_container_width=True)

        if reg_btn:
            if not all([r_name.strip(), r_co.strip(), r_phone.strip(), r_pw.strip()]):
                st.error("All fields are required.")
            elif len(r_pw) < 6:
                st.error("Password must be at least 6 characters.")
            elif r_pw != r_pw2:
                st.error("Passwords don't match.")
            else:
                ok, result = register_user(r_name, r_co, r_phone, r_pw)
                if ok:
                    st.success(f"Account created! Please switch to the Login tab and sign in with **{r_co}**.")
                else:
                    st.error(result)

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ─── ADMIN REDIRECT ───────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.current_user and is_admin(st.session_state.current_user):
    render_admin_dashboard()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# ─── MAIN APP (logged in — regular user) ──────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
user = st.session_state.current_user
user_key = user["key"]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    # User chip
    st.markdown(f"""
<div class="user-chip">
  <div class="user-chip-name"> {user['name']}</div>
  <div class="user-chip-co"> {user['company']}</div>
</div>
""", unsafe_allow_html=True)

    if st.button(" Logout", use_container_width=True):
        for k in ["current_user", "messages", "greeted", "last_spoken_idx",
                   "last_audio_id", "session_id", "loaded_file", "voice_mode"]:
            st.session_state[k] = defaults.get(k, None)
        st.rerun()

    st.markdown("---")
    st.markdown("### API Key")
    api_key_input = st.text_input(
        "key", value=st.session_state.api_key,
        type="password", placeholder="gsk_...",
        label_visibility="collapsed", help="Free at console.groq.com",
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.greeted = False
    if not st.session_state.api_key:
        st.warning("Add your Groq API key to start")
        st.markdown("[Get free key →](https://console.groq.com)")

    st.markdown("---")
    st.markdown("### Model")
    chosen = st.selectbox("m", list(MODEL_OPTIONS.keys()), index=0, label_visibility="collapsed")
    st.session_state.model = MODEL_OPTIONS[chosen]

    st.markdown("---")
    st.markdown("### Voice Mode")
    st.session_state.voice_mode = st.toggle(
        "Enable Voice", value=st.session_state.voice_mode,
        help="Use the mic to speak instead of typing.",
    )
    if st.session_state.voice_mode:
        st.markdown("<small style='color:#a855f7'></small>",
                    unsafe_allow_html=True)

    st.markdown("---")

    # ── Chat History (per user) ────────────────────────────────────────────
    st.markdown("### Chat History")

    if st.button(" New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.greeted = False
        st.session_state.last_audio_id = None
        st.session_state.last_spoken_idx = -1
        st.session_state.session_id = None
        st.session_state.loaded_file = None
        st.rerun()

    histories = list_histories(user_key)

    if not histories:
        st.markdown("<small style='color:#4b5563'>No saved chats yet.</small>",
                    unsafe_allow_html=True)
    else:
        for fname, meta in histories:
            title = meta.get("title", "Untitled")
            ts = meta.get("saved_at", 0)
            date = datetime.fromtimestamp(ts).strftime("%b %d, %I:%M %p") if ts else ""
            n_msg = len(meta.get("messages", []))
            is_cur = (st.session_state.loaded_file == fname)

            col_open, col_del = st.columns([5, 1])
            with col_open:
                label = f"{' ' if is_cur else ''}{title}"
                if st.button(label, key=f"load_{fname}", use_container_width=True,
                             help=f"{n_msg} messages · {date}"):
                    data = load_history_file(user_key, fname)
                    st.session_state.messages = data["messages"]
                    st.session_state.greeted = True
                    st.session_state.last_spoken_idx = len(data["messages"]) - 1
                    st.session_state.last_audio_id = None
                    st.session_state.session_id = fname.replace(".json", "")
                    st.session_state.loaded_file = fname
                    st.rerun()
            with col_del:
                if st.button("", key=f"del_{fname}", help="Delete"):
                    delete_history_file(user_key, fname)
                    if st.session_state.loaded_file == fname:
                        st.session_state.messages = []
                        st.session_state.greeted = False
                        st.session_state.session_id = None
                        st.session_state.loaded_file = None
                    st.rerun()

    st.markdown("---")
    st.markdown(f"**Messages:** {len(st.session_state.messages)}")
    st.markdown("<small>CRM Consultant · Groq + Llama 3 · Edge-TTS</small>", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="aria-header">
  <div class="aria-logo"></div>
  <div>
    <p class="aria-name">&nbsp;<span style="font-weight:400;color:#6b7280;font-size:.9rem;">CRM Assistant</span></p>
    <p class="aria-status"><span class="dot-green"></span>Online</p>
  </div>
</div>
""", unsafe_allow_html=True)

if st.session_state.voice_mode:
    st.markdown(
        '<div class="voice-badge"><div class="pulse"></div> Voice Mode Active</div>',
        unsafe_allow_html=True,
    )


# ─── Helper Functions ─────────────────────────────────────────────────────────

def auto_save():
    """Auto-save the current chat session."""
    msgs = st.session_state.messages
    if not msgs:
        return
    if not st.session_state.session_id:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    sid = st.session_state.session_id
    title = make_title(msgs)
    save_history(user_key, sid, msgs, title)
    st.session_state.loaded_file = f"{sid}.json"


# ─── Auto Greeting ────────────────────────────────────────────────────────────
if not st.session_state.messages and not st.session_state.greeted and st.session_state.api_key:
    with st.spinner("typing…"):
        greeting = call_ai(st.session_state.api_key, st.session_state.model, [])
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    st.session_state.greeted = True
    auto_save()
    st.rerun()

# ─── No API key ──────────────────────────────────────────────────────────────
if not st.session_state.api_key and not st.session_state.messages:
    st.info("Add your Groq API key in the sidebar to start chatting.")

# ─── Chat Messages (history) ─────────────────────────────────────────────────
summary_present = False

for i, msg in enumerate(st.session_state.messages):
    safe = (msg["content"]
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    if msg["role"] == "user":
        st.markdown(
            f'<div class="msg-user"><div class="bubble-user">{safe}</div></div>',
            unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="msg-bot">
  <div class="bot-av"></div>
  <div class="bubble-bot">{safe}</div>
</div>""", unsafe_allow_html=True)
        if "**Here's everything I've gathered so far:**" in msg["content"]:
            summary_present = True

# ─── Download ────────────────────────────────────────────────────────────────
if summary_present:
    summary_text = next(
        (m["content"] for m in reversed(st.session_state.messages)
         if "**Here's everything I've gathered so far:**" in m["content"]), ""
    )
    st.markdown("<div class='dl-box'>All details collected — download your summary below.</div>",
                unsafe_allow_html=True)
    st.download_button("Download Requirements Summary",
                       data=summary_text.encode("utf-8"),
                       file_name="bigin_crm_requirements.txt",
                       mime="text/plain", use_container_width=True)

# ─── Streaming container (above the input form) ─────────────────────────────
streaming_container = st.container()

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


def handle_user_message(user_msg: str, voice_reply: bool = False):
    """Process a user message: stream LLM response, save, and rerun."""
    st.session_state.messages.append({"role": "user", "content": user_msg})

    # Stream into the container that sits ABOVE the input
    with streaming_container:
        safe_user = user_msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f'<div class="msg-user"><div class="bubble-user">{safe_user}</div></div>',
            unsafe_allow_html=True,
        )

        full_response = ""
        message_placeholder = st.empty()

        for token in stream_ai(st.session_state.api_key, st.session_state.model,
                               st.session_state.messages):
            full_response += token
            safe = (full_response
                    .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            message_placeholder.markdown(f"""
<div class="msg-bot">
  <div class="bot-av"></div>
  <div class="bubble-bot">{safe}<span class="streaming-dot"></span></div>
</div>""", unsafe_allow_html=True)

    # Save to state
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.last_spoken_idx = len(st.session_state.messages) - 1

    # Generate TTS for voice loop (will be sent to component on rerun)
    if voice_reply and full_response:
        mp3_bytes = synthesize(full_response)
        if mp3_bytes:
            st.session_state.voice_tts_b64 = base64.b64encode(mp3_bytes).decode("utf-8")
        else:
            st.session_state.voice_tts_b64 = ""
    else:
        st.session_state.voice_tts_b64 = ""

    auto_save()
    st.rerun()


# ─── Voice Mode: Auto Voice Loop Component ───────────────────────────────────
if st.session_state.voice_mode:
    st.markdown("---")

    # Render the voice component — it auto-plays TTS and returns recorded audio
    tts_to_play = st.session_state.get("voice_tts_b64", "")

    # Clear TTS after sending (so it doesn't replay on rerun)
    if tts_to_play:
        st.session_state.voice_tts_b64 = ""

    voice_result = voice_loop_component(
        tts_audio_b64=tts_to_play,
        key="voice_loop",
    )

    # Process captured audio from the component (deduplicate by timestamp)
    if voice_result and isinstance(voice_result, dict) and voice_result.get("audio_b64"):
        ts = voice_result.get("timestamp", 0)
        last_ts = st.session_state.get("voice_last_ts", 0)

        if ts != last_ts:
            # New audio — process it
            st.session_state.voice_last_ts = ts
            audio_b64 = voice_result["audio_b64"]
            audio_bytes = base64.b64decode(audio_b64)

            with st.spinner("Transcribing..."):
                transcript = call_stt(st.session_state.api_key, audio_bytes)

            if transcript and not transcript.startswith("[Transcription error"):
                handle_user_message(transcript, voice_reply=True)
            else:
                st.warning("Couldn't understand — listening again...")
                st.rerun()

# ─── Text Input (always available as fallback) ────────────────────────────────
with st.form("chat_form", clear_on_submit=True):
    c1, c2 = st.columns([8, 2])
    with c1:
        user_input = st.text_input("msg", placeholder="Type your message…",
                                   label_visibility="collapsed")
    with c2:
        submitted = st.form_submit_button("Send ➤", use_container_width=True)

if submitted and user_input.strip():
    handle_user_message(user_input.strip(), voice_reply=st.session_state.voice_mode)
