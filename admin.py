# ─── admin.py ─────────────────────────────────────────────────────────────────
# Admin dashboard — mirrors the regular user interface.
# Sidebar: users list → chat sessions → click to view chat in bubble format.
# ──────────────────────────────────────────────────────────────────────────────

import streamlit as st
from datetime import datetime
from auth import (
    list_all_users, list_histories, load_history_file,
    delete_history_file, is_admin,
)


def render_admin_dashboard():
    """Render admin dashboard that mirrors the regular user chat interface."""
    user = st.session_state.current_user

    # ── Security gate ──
    if not user or not is_admin(user):
        st.error("Access denied. Admin privileges required.")
        st.stop()

    # ── Session state defaults for admin ──
    if "admin_selected_user" not in st.session_state:
        st.session_state.admin_selected_user = None
    if "admin_loaded_chat" not in st.session_state:
        st.session_state.admin_loaded_chat = None
    if "admin_messages" not in st.session_state:
        st.session_state.admin_messages = []
    if "admin_chat_title" not in st.session_state:
        st.session_state.admin_chat_title = ""

    # ── Sidebar ──
    with st.sidebar:
        # Admin chip
        st.markdown(f"""
        <div class="user-chip">
          <div class="user-chip-name">{user['name']}</div>
          <div class="user-chip-co">{user['company']}
            <span style="background:rgba(220,38,38,.15);border:1px solid rgba(220,38,38,.3);
              color:#fca5a5;border-radius:20px;padding:2px 8px;font-size:0.7rem;
              font-weight:600;margin-left:6px;">ADMIN</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Logout", use_container_width=True, key="admin_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.markdown("---")

        # ── Users list ──
        st.markdown("### Users")

        try:
            all_users = list_all_users()
        except Exception:
            all_users = []

        regular_users = [u for u in all_users if u.get("role") != "admin"]

        if not regular_users:
            st.markdown(
                "<small style='color:#4b5563'>No users registered yet.</small>",
                unsafe_allow_html=True,
            )
        else:
            # "All Users" button to go back
            if st.session_state.admin_selected_user is not None:
                if st.button("← Back to Users", use_container_width=True, key="admin_back"):
                    st.session_state.admin_selected_user = None
                    st.session_state.admin_loaded_chat = None
                    st.session_state.admin_messages = []
                    st.session_state.admin_chat_title = ""
                    st.rerun()

            if st.session_state.admin_selected_user is None:
                # Show user list
                for u in regular_users:
                    # Count chats for this user
                    try:
                        user_chats = list_histories(u["key"])
                        chat_count = len(user_chats)
                    except Exception:
                        chat_count = 0

                    label = f"{u['company']} ({u['name']})"
                    if st.button(
                        label,
                        key=f"admin_user_{u['key']}",
                        use_container_width=True,
                        help=f"{chat_count} chat(s)",
                    ):
                        st.session_state.admin_selected_user = u
                        st.session_state.admin_loaded_chat = None
                        st.session_state.admin_messages = []
                        st.session_state.admin_chat_title = ""
                        st.rerun()

            else:
                # Show chat history for selected user
                sel_user = st.session_state.admin_selected_user
                st.markdown(f"### {sel_user['company']}")
                st.markdown(
                    f"<small style='color:#6b7280'>{sel_user['name']}</small>",
                    unsafe_allow_html=True,
                )
                st.markdown("---")
                st.markdown("### Chat History")

                try:
                    histories = list_histories(sel_user["key"])
                except Exception:
                    histories = []

                if not histories:
                    st.markdown(
                        "<small style='color:#4b5563'>No chats yet.</small>",
                        unsafe_allow_html=True,
                    )
                else:
                    for fname, meta in histories:
                        title = meta.get("title", "Untitled")
                        ts = meta.get("saved_at", 0)
                        date = (
                            datetime.fromtimestamp(ts).strftime("%b %d, %I:%M %p")
                            if ts else ""
                        )
                        n_msg = len(meta.get("messages", []))
                        is_cur = st.session_state.admin_loaded_chat == fname

                        col_open, col_del = st.columns([5, 1])
                        with col_open:
                            label = f"{'● ' if is_cur else ''}{title}"
                            if st.button(
                                label,
                                key=f"admin_load_{sel_user['key']}_{fname}",
                                use_container_width=True,
                                help=f"{n_msg} messages · {date}",
                            ):
                                try:
                                    data = load_history_file(sel_user["key"], fname)
                                    st.session_state.admin_messages = data["messages"]
                                    st.session_state.admin_loaded_chat = fname
                                    st.session_state.admin_chat_title = title
                                except Exception:
                                    st.session_state.admin_messages = []
                                st.rerun()
                        with col_del:
                            if st.button(
                                "🗑",
                                key=f"admin_del_{sel_user['key']}_{fname}",
                                help="Delete",
                            ):
                                try:
                                    delete_history_file(sel_user["key"], fname)
                                except Exception:
                                    pass
                                if st.session_state.admin_loaded_chat == fname:
                                    st.session_state.admin_messages = []
                                    st.session_state.admin_loaded_chat = None
                                    st.session_state.admin_chat_title = ""
                                st.rerun()

        st.markdown("---")
        if st.session_state.admin_selected_user:
            st.markdown(
                f"**Messages:** {len(st.session_state.admin_messages)}"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # ─── Main Content Area ────────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════════

    # Header — same look as user UI
    st.markdown("""
    <div class="aria-header">
      <div class="aria-logo"></div>
      <div>
        <p class="aria-name">&nbsp;<span style="font-weight:400;color:#6b7280;font-size:.9rem;">Admin Dashboard</span></p>
        <p class="aria-status"><span class="dot-green"></span>Viewing chats</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── No user selected — show overview ──
    if st.session_state.admin_selected_user is None:
        try:
            all_users = list_all_users()
        except Exception:
            all_users = []

        regular_users = [u for u in all_users if u.get("role") != "admin"]

        st.markdown(
            "<div style='text-align:center;padding:40px 0 20px;color:#6b7280;"
            "font-size:0.95rem;'>Select a user from the sidebar to view their chats</div>",
            unsafe_allow_html=True,
        )

        # Show a nice user overview
        for u in regular_users:
            try:
                user_chats = list_histories(u["key"])
                chat_count = len(user_chats)
                total_msgs = sum(len(m.get("messages", [])) for _, m in user_chats)
            except Exception:
                chat_count = 0
                total_msgs = 0

            created = ""
            if u.get("created_at"):
                try:
                    dt = datetime.fromisoformat(
                        u["created_at"].replace("Z", "+00:00")
                    )
                    created = dt.strftime("%b %d, %Y")
                except Exception:
                    pass

            st.markdown(f"""
            <div style="background:#1c1c2a;border:1px solid #2a2a3e;border-radius:14px;
                 padding:16px 18px;margin-bottom:10px;">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <span style="color:#f1f5f9;font-weight:600;font-size:0.92rem;">
                    {u['name']}</span>
                  <span style="color:#6b7280;font-size:0.82rem;margin-left:8px;">
                    {u['company']}</span>
                </div>
                <span style="color:#4b5563;font-size:0.75rem;">{created}</span>
              </div>
              <div style="margin-top:8px;display:flex;gap:16px;">
                <span style="color:#c4b5fd;font-size:0.8rem;">
                  {chat_count} chat(s)</span>
                <span style="color:#9ca3af;font-size:0.8rem;">
                  {total_msgs} message pairs</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        return

    # ── User selected but no chat loaded ──
    if not st.session_state.admin_messages:
        sel = st.session_state.admin_selected_user
        st.markdown(
            f"<div style='text-align:center;padding:40px 0;color:#6b7280;"
            f"font-size:0.9rem;'>Select a chat from <b>{sel['company']}</b>'s "
            f"history in the sidebar</div>",
            unsafe_allow_html=True,
        )
        return

    # ── Chat loaded — render in exact user bubble format ──
    sel = st.session_state.admin_selected_user
    st.markdown(
        f"<div style='color:#6b7280;font-size:0.78rem;margin-bottom:12px;'>"
        f"Viewing: <b>{st.session_state.admin_chat_title}</b> "
        f"by <b>{sel['company']}</b> ({sel['name']})</div>",
        unsafe_allow_html=True,
    )

    for msg in st.session_state.admin_messages:
        safe = (
            msg["content"]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        if msg["role"] == "user":
            st.markdown(
                f'<div class="msg-user"><div class="bubble-user">{safe}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class="msg-bot">
  <div class="bot-av"></div>
  <div class="bubble-bot">{safe}</div>
</div>""",
                unsafe_allow_html=True,
            )
