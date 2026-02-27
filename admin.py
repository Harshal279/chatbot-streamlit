# ─── admin.py ─────────────────────────────────────────────────────────────────
# Admin dashboard — view, filter, search, and delete all user chats.
# Called from app.py when authenticated user has role == "admin".
# ──────────────────────────────────────────────────────────────────────────────

import streamlit as st
from datetime import datetime
from auth import list_all_users, list_all_chats, admin_delete_chat, is_admin


# ─── Admin CSS ──────────────────────────────────────────────────────────────

ADMIN_CSS = """
<style>
/* ── Stat Cards ── */
.stat-row { display: flex; gap: 14px; margin-bottom: 24px; }
.stat-card {
    flex: 1;
    background: #1c1c2a;
    border: 1px solid #2a2a3e;
    border-radius: 16px;
    padding: 20px 18px;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem; font-weight: 700;
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.stat-label { color: #6b7280; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }

/* ── Chat Card ── */
.chat-card {
    background: #1c1c2a;
    border: 1px solid #2a2a3e;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.chat-card:hover { border-color: #7c3aed; }
.chat-meta {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 10px;
}
.chat-user {
    color: #c4b5fd; font-size: 0.82rem; font-weight: 600;
    background: rgba(124,58,237,.12);
    border: 1px solid rgba(124,58,237,.25);
    border-radius: 8px;
    padding: 3px 10px;
}
.chat-time { color: #4b5563; font-size: 0.75rem; }
.chat-msg-label { color: #6b7280; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 3px; }
.chat-msg-content {
    color: #d1d5db; font-size: 0.85rem; line-height: 1.55;
    background: #13131f;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    max-height: 120px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}
.chat-msg-user { border-left: 3px solid #7c3aed; }
.chat-msg-bot  { border-left: 3px solid #22c55e; }

/* ── Admin Header ── */
.admin-header {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 0 18px;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 22px;
}
.admin-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, #dc2626, #f97316);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 16px rgba(220,38,38,.35);
    flex-shrink: 0;
}
.admin-title { font-size: 1.05rem; font-weight: 700; color: #f1f5f9; margin: 0; }
.admin-sub   { font-size: 0.75rem; color: #6b7280; margin: 0; }
.admin-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(220,38,38,.12);
    border: 1px solid rgba(220,38,38,.3);
    color: #fca5a5; border-radius: 20px;
    padding: 3px 10px; font-size: 0.72rem; font-weight: 600;
}

/* ── Empty state ── */
.empty-state {
    text-align: center; padding: 48px 16px;
    color: #4b5563; font-size: 0.9rem;
}

/* ── No results ── */
.no-results {
    text-align: center; padding: 32px; color: #6b7280;
    background: #1c1c2a; border-radius: 14px; border: 1px solid #2a2a3e;
}
</style>
"""


def render_admin_dashboard():
    """Render the full admin dashboard. Called from app.py after role check."""
    user = st.session_state.current_user

    # ── Security gate ──
    if not user or not is_admin(user):
        st.error("Access denied. Admin privileges required.")
        st.stop()

    st.markdown(ADMIN_CSS, unsafe_allow_html=True)

    # ── Header ──
    st.markdown("""
    <div class="admin-header">
      <div class="admin-logo"></div>
      <div>
        <p class="admin-title">Admin Dashboard</p>
        <p class="admin-sub">Manage users and view all conversations</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar ──
    with st.sidebar:
        st.markdown(f"""
        <div class="user-chip">
          <div class="user-chip-name">{user['name']}</div>
          <div class="user-chip-co">{user['company']} <span class="admin-badge">ADMIN</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Logout", use_container_width=True, key="admin_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown("---")

    # ── Load data ──
    try:
        all_users = list_all_users()
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        all_users = []

    # ── Stats ──
    total_users = len([u for u in all_users if u.get("role") != "admin"])
    total_admins = len([u for u in all_users if u.get("role") == "admin"])

    try:
        all_chats_count = list_all_chats(limit=1000)
        total_chats = len(all_chats_count)
        total_messages = sum(1 for c in all_chats_count if c.get("user_message")) + \
                         sum(1 for c in all_chats_count if c.get("assistant_response"))
    except Exception:
        total_chats = 0
        total_messages = 0

    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-number">{total_users}</div>
        <div class="stat-label">Users</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{total_admins}</div>
        <div class="stat-label">Admins</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{total_chats}</div>
        <div class="stat-label">Chat Pairs</div>
      </div>
      <div class="stat-card">
        <div class="stat-number">{total_messages}</div>
        <div class="stat-label">Messages</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Filters ──
    col_filter, col_search = st.columns([1, 2])

    with col_filter:
        user_options = ["All Users"] + [
            f"{u['company']} ({u['name']})" for u in all_users if u.get("role") != "admin"
        ]
        user_keys_map = {
            f"{u['company']} ({u['name']})": u["key"]
            for u in all_users if u.get("role") != "admin"
        }
        selected_user = st.selectbox("Filter by user", user_options, key="admin_user_filter")

    with col_search:
        search_query = st.text_input(
            "Search chats",
            placeholder="Search messages...",
            key="admin_search",
        )

    # ── Prepare filter params ──
    user_filter = None
    if selected_user != "All Users":
        user_filter = user_keys_map.get(selected_user)

    # ── Fetch chats ──
    try:
        chats = list_all_chats(
            user_filter=user_filter,
            search_query=search_query.strip() if search_query else None,
            limit=200,
        )
    except Exception as e:
        st.error(f"Failed to load chats: {e}")
        chats = []

    st.markdown("---")

    # ── Results count ──
    if search_query:
        st.markdown(
            f"<small style='color:#6b7280;'>Showing {len(chats)} result(s) for \"{search_query}\"</small>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"<small style='color:#6b7280;'>Showing {len(chats)} chat pair(s)</small>",
            unsafe_allow_html=True,
        )

    # ── Chat list ──
    if not chats:
        st.markdown(
            '<div class="no-results">No chats found.</div>',
            unsafe_allow_html=True,
        )
    else:
        for chat in chats:
            _render_chat_card(chat)


def _render_chat_card(chat: dict):
    """Render a single chat card with user info, messages, and delete button."""
    chat_id = chat.get("id", 0)
    user_key = chat.get("user_key", "unknown")
    user_msg = chat.get("user_message", "")
    bot_msg = chat.get("assistant_response", "")
    created = chat.get("created_at", "")

    # Format timestamp
    try:
        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        time_str = dt.strftime("%b %d, %Y · %I:%M %p")
    except Exception:
        time_str = created

    # Escape HTML
    safe_user = (user_msg or "(no message)").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_bot  = (bot_msg or "(no response)").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Truncate for display
    display_user = safe_user[:300] + ("..." if len(safe_user) > 300 else "")
    display_bot  = safe_bot[:300] + ("..." if len(safe_bot) > 300 else "")

    st.markdown(f"""
    <div class="chat-card">
      <div class="chat-meta">
        <span class="chat-user">{user_key}</span>
        <span class="chat-time">{time_str}</span>
      </div>
      <div class="chat-msg-label">User Message</div>
      <div class="chat-msg-content chat-msg-user">{display_user}</div>
      <div class="chat-msg-label">Assistant Response</div>
      <div class="chat-msg-content chat-msg-bot">{display_bot}</div>
    </div>
    """, unsafe_allow_html=True)

    # Delete button
    if st.button(f"Delete", key=f"admin_del_{chat_id}", help="Permanently delete this chat"):
        try:
            admin_delete_chat(chat_id)
            st.success("Chat deleted.")
            st.rerun()
        except Exception as e:
            st.error(f"Delete failed: {e}")
