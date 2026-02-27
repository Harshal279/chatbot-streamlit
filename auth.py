# ─── auth.py ──────────────────────────────────────────────────────────────────
# User authentication and chat history — backed by Supabase (PostgreSQL).
# ──────────────────────────────────────────────────────────────────────────────

import re
import hashlib
import time
from datetime import datetime, timezone

from db import supabase


# ─── Password & Key Helpers ─────────────────────────────────────────────────

def hash_pw(pw: str) -> str:
    """SHA-256 hash of a password string."""
    return hashlib.sha256(pw.strip().encode()).hexdigest()


def company_key(company: str) -> str:
    """Normalised key from company name (used as login ID)."""
    return re.sub(r"[^a-z0-9_]", "_", company.strip().lower())


# ─── User CRUD ──────────────────────────────────────────────────────────────

def register_user(name: str, company: str, phone: str, password: str) -> tuple[bool, str]:
    """Register a new user with role='user'. Returns (success, key_or_error)."""
    key = company_key(company)
    if not key:
        return False, "Company name is invalid."

    # Check if company already exists
    try:
        existing = supabase.table("users").select("id").eq("key", key).execute()
        if existing.data:
            return False, "A company with that name is already registered."
    except Exception as e:
        return False, f"Database connection error. Please try again. ({type(e).__name__})"

    try:
        supabase.table("users").insert({
            "key": key,
            "name": name.strip(),
            "company": company.strip(),
            "phone": phone.strip(),
            "pw_hash": hash_pw(password),
            "role": "user",
        }).execute()
        return True, key
    except Exception as e:
        return False, f"Registration failed: {e}"


def login_user(company: str, password: str) -> tuple[bool, str, dict]:
    """Authenticate a user. Returns (success, key_or_error, user_dict)."""
    key = company_key(company)
    try:
        result = supabase.table("users").select("*").eq("key", key).execute()
    except Exception as e:
        return False, f"Database connection error. Please try again. ({type(e).__name__})", {}

    if not result.data:
        return False, "Company not found. Please register first.", {}

    user = result.data[0]
    if user["pw_hash"] != hash_pw(password):
        return False, "Wrong password.", {}

    return True, key, {
        "key": user["key"],
        "name": user["name"],
        "company": user["company"],
        "phone": user["phone"],
        "role": user.get("role", "user"),
    }


def is_admin(user: dict) -> bool:
    """Check if a user dict has the admin role."""
    return user.get("role") == "admin"


def seed_admin(name: str, company: str, phone: str, password: str) -> str:
    """Create an admin account. Run once from Python REPL or a script."""
    key = company_key(company)
    existing = supabase.table("users").select("id").eq("key", key).execute()
    if existing.data:
        # Update existing user to admin
        supabase.table("users").update({"role": "admin"}).eq("key", key).execute()
        return f"User '{key}' promoted to admin."

    supabase.table("users").insert({
        "key": key,
        "name": name.strip(),
        "company": company.strip(),
        "phone": phone.strip(),
        "pw_hash": hash_pw(password),
        "role": "admin",
    }).execute()
    return f"Admin '{key}' created."


# ─── Chat History (per-user) ────────────────────────────────────────────────

def save_history(user_key: str, session_id: str, messages: list, title: str):
    """
    Save/update a chat session to Supabase.
    Upserts message pairs (user + assistant) from the conversation.
    """
    try:
        # Delete existing messages for this session (full replace strategy)
        supabase.table("chats").delete().eq("user_key", user_key).eq("session_id", session_id).execute()

        # Build rows — pair up user messages with the following assistant response
        rows = []
        i = 0
        while i < len(messages):
            msg = messages[i]
            if msg["role"] == "user":
                user_msg = msg["content"]
                assistant_msg = ""
                if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                    assistant_msg = messages[i + 1]["content"]
                    i += 1
                rows.append({
                    "user_key": user_key,
                    "session_id": session_id,
                    "title": title,
                    "user_message": user_msg,
                    "assistant_response": assistant_msg,
                })
            elif msg["role"] == "assistant" and not rows:
                # Greeting or standalone assistant msg (no preceding user msg)
                rows.append({
                    "user_key": user_key,
                    "session_id": session_id,
                    "title": title,
                    "user_message": "",
                    "assistant_response": msg["content"],
                })
            i += 1

        if rows:
            supabase.table("chats").insert(rows).execute()
    except Exception:
        pass  # Silently fail — chat still lives in session state


def list_histories(user_key: str) -> list:
    """
    List all saved chat sessions for a user, newest first.
    Returns list of (session_id_as_filename, meta_dict) for backward compat.
    """
    try:
        result = (
            supabase.table("chats")
            .select("session_id, title, created_at")
            .eq("user_key", user_key)
            .order("created_at", desc=True)
            .execute()
        )
    except Exception:
        return []  # Return empty on connection error

    # Group by session_id
    sessions = {}
    for row in result.data:
        sid = row["session_id"]
        if sid not in sessions:
            sessions[sid] = {
                "title": row["title"] or "Untitled",
                "saved_at": _iso_to_ts(row["created_at"]),
                "messages": [],  # count placeholder
            }
        sessions[sid]["messages"].append(1)  # just for counting

    # Sort newest first and return in (filename, meta) format
    items = sorted(sessions.items(), key=lambda x: x[1]["saved_at"], reverse=True)
    return [(f"{sid}.json", meta) for sid, meta in items]


def load_history_file(user_key: str, filename: str) -> dict:
    """Load a specific chat session. Returns dict with 'messages' list."""
    session_id = filename.replace(".json", "")
    result = (
        supabase.table("chats")
        .select("user_message, assistant_response, title, created_at")
        .eq("user_key", user_key)
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )

    messages = []
    title = "Untitled"
    for row in result.data:
        title = row.get("title", title)
        if row["user_message"]:
            messages.append({"role": "user", "content": row["user_message"]})
        if row["assistant_response"]:
            messages.append({"role": "assistant", "content": row["assistant_response"]})

    return {"messages": messages, "title": title}


def delete_history_file(user_key: str, filename: str):
    """Delete a saved chat session."""
    session_id = filename.replace(".json", "")
    supabase.table("chats").delete().eq("user_key", user_key).eq("session_id", session_id).execute()


def make_title(messages: list) -> str:
    """Generate a title from the first user message."""
    for m in messages:
        if m["role"] == "user":
            txt = m["content"].strip().replace("\n", " ")
            return txt[:45] + ("…" if len(txt) > 45 else "")
    return "Untitled chat"


# ─── Admin Helpers ──────────────────────────────────────────────────────────

def list_all_users() -> list[dict]:
    """Return all registered users (for admin dashboard)."""
    result = supabase.table("users").select("key, name, company, phone, role, created_at").order("created_at", desc=True).execute()
    return result.data


def list_all_chats(user_filter: str = None, search_query: str = None, limit: int = 100) -> list[dict]:
    """
    Return chats across all users (admin only).
    Optional filter by user_key and/or search text.
    """
    query = supabase.table("chats").select(
        "id, user_key, session_id, title, user_message, assistant_response, created_at"
    )

    if user_filter:
        query = query.eq("user_key", user_filter)

    if search_query:
        # Use ilike for partial matching (Supabase supports this)
        search_term = f"%{search_query}%"
        query = query.or_(
            f"user_message.ilike.{search_term},assistant_response.ilike.{search_term}"
        )

    query = query.order("created_at", desc=True).limit(limit)
    result = query.execute()
    return result.data


def admin_delete_chat(chat_id: int):
    """Delete a specific chat row by ID (admin only)."""
    supabase.table("chats").delete().eq("id", chat_id).execute()


# ─── Internal Helpers ───────────────────────────────────────────────────────

def _iso_to_ts(iso_str: str) -> float:
    """Convert ISO datetime string to Unix timestamp."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0
