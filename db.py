# ─── db.py ────────────────────────────────────────────────────────────────────
# Centralised Supabase client. All modules import `supabase` from here.
# Works with both local .env and Streamlit Cloud secrets.toml.
# ──────────────────────────────────────────────────────────────────────────────

import os
import streamlit as st
from supabase import create_client, Client

# Try st.secrets first (Streamlit Cloud), then fall back to .env (local dev)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_KEY must be set in "
        ".streamlit/secrets.toml (cloud) or .env (local)."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
