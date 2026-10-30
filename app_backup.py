import asyncio
import os
import uuid

import streamlit as st

from marketing_agents.service import (
    stream_marketing_response,
    list_conversations,
    list_hidden_conversations,
    get_conversation_history,
    hide_conversation,
    restore_conversation,
    rename_conversation,
)

from tools.human_approval import (
    list_pending_requests,
    list_all_requests,
    decide_approval,
)


# =========================================
# PAGE CONFIGURATION
# =========================================

st.set_page_config(
    page_title="AI Marketing Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================
# CUSTOM DESIGN
# =========================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0e1117;
    }

    [data-testid="stSidebar"] {
        background-color: #161b26;
    }

    .main-title {
        font-size: 36px;
        font-weight: 800;
        color: white;
    }

    .subtitle {
        color: #a5b0c2;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .feature-card {
        background: #1b2332;
        border: 1px solid #303b50;
        border-radius: 14px;
        padding: 20px;
        min-height: 135px;
        margin-bottom: 12px;
    }

    .feature-card h3 {
        color: white;
        font-size: 18px;
    }

    .feature-card p {
        color: #a5b0c2;
        font-size: 13px;
    }

    .dashboard-hero {
        background: linear-gradient(
            120deg,
            #172554,
            #312e81,
            #164e63
        );
        border: 1px solid #394b83;
        border-radius: 20px;
        padding: 34px;
        margin-bottom: 25px;
    }

    .dashboard-hero h1 {
        color: white;
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .dashboard-hero p {
        color: #dbeafe;
        font-size: 16px;
    }

    .dashboard-card {
        background: linear-gradient(
            145deg,
            #1b2332,
            #202c40
        );
        border: 1px solid #35445c;
        border-radius: 15px;
        padding: 19px;
        min-height: 145px;
        margin-bottom: 14px;
    }

    .dashboard-card h3 {
        color: #ffffff;
        font-size: 17px;
        margin-bottom: 9px;
    }

    .dashboard-card p {
        color: #aebbd0;
        font-size: 13px;
        min-height: 38px;
    }

    .feature-status {
        color: #86efac;
        font-size: 12px;
        font-weight: 700;
    }

    .section-heading {
        color: white;
        font-size: 23px;
        font-weight: 750;
        margin-top: 18px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================
# PERSISTENT USER ID
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

os.makedirs(MEMORY_DIR, exist_ok=True)

USER_ID_FILE = os.path.join(MEMORY_DIR, "user_id.txt")


def load_or_create_user_id():

    if os.path.exists(USER_ID_FILE):

        with open(USER_ID_FILE, "r", encoding="utf-8") as file:
            saved_user_id = file.read().strip()

        if saved_user_id:
            return saved_user_id

    new_user_id = f"user_{uuid.uuid4().hex[:10]}"

    with open(USER_ID_FILE, "w", encoding="utf-8") as file:
        file.write(new_user_id)

    return new_user_id


# =========================================
# CONVERT STORED HISTORY
# =========================================

def convert_history_items(items):

    messages = []

    for item in items:

        if not isinstance(item, dict):
            continue

        role = item.get("role")

        if role not in ("user", "assistant"):
            continue

        content = item.get("content", "")

        if isinstance(content, str):

            text_content = content

        elif isinstance(content, list):

            text_parts = []

            for part in content:

                if isinstance(part, str):
                    text_parts.append(part)

                elif isinstance(part, dict):

                    text_value = part.get("text")

                    if isinstance(text_value, str):
                        text_parts.append(text_value)

            text_content = "\n".join(text_parts)

        else:
            continue

        if text_content.strip():

            messages.append(
                {
                    "role": role,
                    "content": text_content,
                }
            )

    return messages


# =========================================
# HELPER FUNCTIONS
# =========================================

def open_conversation(conversation_id):

    stored_items = asyncio.run(
        get_conversation_history(
            user_id=st.session_state.user_id,
            session_id=conversation_id,
        )
    )

    st.session_state.session_id = conversation_id

    st.session_state.messages = convert_history_items(
        stored_items
    )

    st.session_state.page = "AI Marketing Chat"
    st.session_state.pending_hide_id = None

    st.rerun()


def create_new_conversation():

    st.session_state.session_id = (
        f"session_{uuid.uuid4().hex[:10]}"
    )

    st.session_state.messages = []
    st.session_state.pending_hide_id = None
    st.session_state.page = "AI Marketing Chat"

    st.rerun()


def filter_conversations(conversations, search_text):

    if not search_text.strip():
        return conversations

    search_text = search_text.lower().strip()

    return [
        conversation
        for conversation in conversations
        if search_text in conversation.get("title", "").lower()
    ]


def format_timestamp(timestamp):

    if not timestamp:
        return "Not available"

    return timestamp.replace("T", " ").split(".")[0]


# =========================================
# SESSION STATE
# =========================================

if "user_id" not in st.session_state:
    st.session_state.user_id = load_or_create_user_id()

if "session_id" not in st.session_state:
    st.session_state.session_id = (
        f"session_{uuid.uuid4().hex[:10]}"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "pending_hide_id" not in st.session_state:
    st.session_state.pending_hide_id = None


# =========================================
# SIDEBAR
# =========================================

with st.sidebar:

    st.title("🚀 AI Marketing Agent")

    st.caption("Your intelligent marketing assistant")

    st.divider()

    st.subheader("Navigation")

    pages = [
        "Dashboard",
        "AI Marketing Chat",
        "Human Approval",
        "About",
    ]

    selected_page = st.radio(
        "Select Page",
        pages,
        index=pages.index(st.session_state.page),
        format_func=lambda page: (
            "🤝 Human Approval"
            if page == "Human Approval"
            else page
        ),
        label_visibility="collapsed",
    )

    st.session_state.page = selected_page

    st.divider()

    # CONVERSATION MANAGEMENT

    st.subheader("Conversations")

    if st.button(
        "➕ New Conversation",
        use_container_width=True,
        type="primary",
    ):
        create_new_conversation()

    search_text = st.text_input(
        "🔎 Search conversations",
        placeholder="Search by title...",
        key="conversation_search",
    )

    user_id = st.session_state.user_id

    try:

        conversations = list_conversations(user_id)

        filtered_conversations = filter_conversations(
            conversations,
            search_text,
        )

        st.caption("📂 Previous Conversations")

        if filtered_conversations:

            for conversation in filtered_conversations:

                conversation_id = conversation["session_id"]
                conversation_title = conversation["title"]

                is_active = (
                    conversation_id
                    == st.session_state.session_id
                )

                button_label = (
                    f"📌 {conversation_title[:35]}"
                    if is_active
                    else f"💬 {conversation_title[:35]}"
                )

                if st.button(
                    button_label,
                    key=f"history_{conversation_id}",
                    use_container_width=True,
                ):

                    open_conversation(conversation_id)

                with st.expander(
                    f"⚙️ Manage: {conversation_title[:22]}",
                    expanded=(
                        st.session_state.pending_hide_id
                        == conversation_id
                    ),
                ):

                    with st.form(
                        key=f"rename_form_{conversation_id}"
                    ):

                        new_title = st.text_input(
                            "New conversation name",
                            value=conversation_title,
                            max_chars=80,
                        )

                        rename_submitted = st.form_submit_button(
                            "✏️ Rename Conversation",
                            use_container_width=True,
                        )

                        if rename_submitted:

                            if not new_title.strip():

                                st.error(
                                    "Conversation name cannot be empty."
                                )

                            else:

                                try:

                                    rename_conversation(
                                        user_id,
                                        conversation_id,
                                        new_title.strip(),
                                    )

                                    st.success(
                                        "Conversation renamed!"
                                    )

                                    st.rerun()

                                except Exception as error:

                                    st.error(
                                        f"Rename failed: {error}"
                                    )

                    st.divider()

                    if (
                        st.session_state.pending_hide_id
                        != conversation_id
                    ):

                        if st.button(
                            "🙈 Hide Conversation",
                            key=f"hide_{conversation_id}",
                            use_container_width=True,
                        ):

                            st.session_state.pending_hide_id = (
                                conversation_id
                            )

                            st.rerun()

                    else:

                        st.warning(
                            "Hide this conversation? "
                            "Saved messages will not be deleted."
                        )

                        confirm_col, cancel_col = st.columns(2)

                        with confirm_col:

                            if st.button(
                                "Yes, Hide",
                                key=f"confirm_hide_{conversation_id}",
                                type="primary",
                                use_container_width=True,
                            ):

                                try:

                                    hide_conversation(
                                        user_id,
                                        conversation_id,
                                    )

                                    if (
                                        conversation_id
                                        == st.session_state.session_id
                                    ):

                                        st.session_state.session_id = (
                                            f"session_{uuid.uuid4().hex[:10]}"
                                        )

                                        st.session_state.messages = []

                                        st.session_state.page = (
                                            "AI Marketing Chat"
                                        )

                                    st.session_state.pending_hide_id = None

                                    st.rerun()

                                except Exception as error:

                                    st.error(
                                        f"Could not hide conversation: {error}"
                                    )

                        with cancel_col:

                            if st.button(
                                "Cancel",
                                key=f"cancel_hide_{conversation_id}",
                                use_container_width=True,
                            ):

                                st.session_state.pending_hide_id = None

                                st.rerun()

        else:

            if search_text.strip():
                st.caption("No matching conversations found.")
            else:
                st.caption("No previous conversations yet.")

        # HIDDEN CHATS

        st.divider()

        with st.expander("🙈 Hidden Chats", expanded=False):

            hidden_conversations = list_hidden_conversations(
                user_id
            )

            filtered_hidden = filter_conversations(
                hidden_conversations,
                search_text,
            )

            if filtered_hidden:

                for conversation in filtered_hidden:

                    hidden_id = conversation["session_id"]
                    hidden_title = conversation["title"]

                    st.write(f"📦 {hidden_title[:35]}")

                    restore_col, open_col = st.columns(2)

                    with restore_col:

                        if st.button(
                            "↩️ Restore",
                            key=f"restore_{hidden_id}",
                            use_container_width=True,
                        ):

                            try:

                                restore_conversation(
                                    user_id,
                                    hidden_id,
                                )

                                st.success("Conversation restored!")
                                st.rerun()

                            except Exception as error:

                                st.error(
                                    f"Restore failed: {error}"
                                )

                    with open_col:

                        if st.button(
                            "💬 Open",
                            key=f"open_hidden_{hidden_id}",
                            use_container_width=True,
                        ):

                            open_conversation(hidden_id)

            else:

                st.caption("No hidden conversations.")

    except Exception as error:

        st.warning(
            f"Could not load conversation history: {error}"
        )

    st.divider()

    st.subheader("Account")

    st.caption("User ID")
    st.code(st.session_state.user_id)

    st.caption("Session ID")
    st.code(st.session_state.session_id)

    st.divider()

    st.caption("AI Marketing Agent | Development Version")


# =========================================
# DASHBOARD
# =========================================

if st.session_state.page == "Dashboard":

    try:
        dashboard_conversations = list_conversations(
            st.session_state.user_id
        )

        dashboard_hidden = list_hidden_conversations(
            st.session_state.user_id
        )

        dashboard_pending = list_pending_requests()
        dashboard_all_approvals = list_all_requests()

        approved_total = sum(
            1 for item in dashboard_all_approvals
            if item["status"] == "approved"
        )

        rejected_total = sum(
            1 for item in dashboard_all_approvals
            if item["status"] == "rejected"
        )

    except Exception as error:

        dashboard_conversations = []
        dashboard_hidden = []
        dashboard_pending = []
        approved_total = 0
        rejected_total = 0

        st.warning(
            f"Some dashboard statistics could not load: {error}"
        )

    # HERO SECTION

    st.markdown(
        """
        <div class="dashboard-hero">
            <h1>🚀 AI Marketing Dashboard</h1>
            <p>
                Your intelligent workspace for smarter marketing,
                creative content and business growth.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-heading">📊 Project Overview</div>',
        unsafe_allow_html=True,
    )

    # METRICS

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "💬 Conversations",
        len(dashboard_conversations),
    )

    metric2.metric(
        "⏳ Pending Approvals",
        len(dashboard_pending),
    )

    metric3.metric(
        "✅ Approved",
        approved_total,
    )

    metric4.metric(
        "🙈 Hidden Chats",
        len(dashboard_hidden),
    )

    st.divider()

    st.markdown(
        '<div class="section-heading">⚡ AI Capabilities</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Explore the tools and capabilities available in your AI Marketing Agent."
    )

    features = [
        (
            "✍️ AI Marketing Responses",
            "Generate marketing ideas, strategies and business content.",
        ),
        (
            "⚡ Streaming Responses",
            "Receive AI responses progressively in real time.",
        ),
        (
            "🧠 Conversation Memory",
            "Maintain conversation context and session history.",
        ),
        (
            "🛠️ Tool Calling",
            "Use specialized tools to complete marketing tasks.",
        ),
        (
            "🤝 Multi-Agent Handoffs",
            "Delegate caption writing and content planning tasks.",
        ),
        (
            "🎙️ Realtime Voice",
            "Interact with your AI agent using voice capabilities.",
        ),
        (
            "🎨 Image Generation",
            "Generate promotional images for marketing campaigns.",
        ),
        (
            "📁 Business Document Search",
            "Find useful information in uploaded business documents.",
        ),
        (
            "🌐 Web Research",
            "Research current marketing information and trends.",
        ),
        (
            "🛡️ Input Guardrails",
            "Validate user inputs before processing requests.",
        ),
        (
            "🙋 Human Approval",
            "Review proposed actions before external execution.",
        ),
        (
            "📈 Agent Tracing",
            "Inspect agent runs and trace execution activity.",
        ),
    ]

    for row_start in range(0, len(features), 3):

        columns = st.columns(3)

        for column_index, column in enumerate(columns):

            feature_index = row_start + column_index

            if feature_index >= len(features):
                break

            feature_name, feature_description = features[
                feature_index
            ]

            with column:

                st.markdown(
                    f"""
                    <div class="dashboard-card">
                        <h3>{feature_name}</h3>
                        <p>{feature_description}</p>
                        <div class="feature-status">
                            ● Backend capability implemented
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    # QUICK ACTIONS

    st.markdown(
        '<div class="section-heading">🚀 Quick Actions</div>',
        unsafe_allow_html=True,
    )

    action_col1, action_col2, action_col3 = st.columns(3)

    with action_col1:

        if st.button(
            "💬 Open AI Marketing Chat",
            use_container_width=True,
            type="primary",
        ):

            st.session_state.page = "AI Marketing Chat"
            st.rerun()

    with action_col2:

        if st.button(
            "🤝 Open Human Approval",
            use_container_width=True,
        ):

            st.session_state.page = "Human Approval"
            st.rerun()

    with action_col3:

        if st.button(
            "ℹ️ About Project",
            use_container_width=True,
        ):

            st.session_state.page = "About"
            st.rerun()

    st.divider()

    st.caption(
        "AI Marketing Agent | Intelligent Marketing Workspace | Development Version"
    )


# =========================================
# AI MARKETING CHAT
# =========================================

elif st.session_state.page == "AI Marketing Chat":

    st.title("💬 AI Marketing Chat")

    st.caption(
        "Ask questions, create marketing strategies, "
        "and generate business content."
    )

    if st.session_state.messages:

        if st.button("🧹 Clear Chat View"):

            st.session_state.messages = []
            st.rerun()

        st.caption(
            "Clear Chat View only clears messages from this screen. "
            "Saved conversation history remains available."
        )

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    user_prompt = st.chat_input(
        "Ask your AI Marketing Agent..."
    )

    if user_prompt:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

        with st.chat_message("user"):

            st.markdown(user_prompt)

        with st.chat_message("assistant"):

            response_placeholder = st.empty()

            try:

                async def stream_response():

                    chunks = []

                    async for chunk in stream_marketing_response(
                        user_message=user_prompt,
                        user_id=st.session_state.user_id,
                        session_id=st.session_state.session_id,
                    ):

                        chunks.append(chunk)

                        response_placeholder.markdown(
                            "".join(chunks) + "▌"
                        )

                    return "".join(chunks)

                full_response = asyncio.run(
                    stream_response()
                )

                response_placeholder.markdown(
                    full_response
                )

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": full_response,
                    }
                )

            except Exception as error:

                st.error(
                    f"Something went wrong: {error}"
                )


# =========================================
# HUMAN APPROVAL DASHBOARD
# =========================================

elif st.session_state.page == "Human Approval":

    st.title("🤝 Human Approval Dashboard")

    st.caption(
        "Review proposed business actions before any external action is taken."
    )

    try:

        pending_requests = list_pending_requests()
        all_requests = list_all_requests()

        approved_count = sum(
            1 for request in all_requests
            if request["status"] == "approved"
        )

        rejected_count = sum(
            1 for request in all_requests
            if request["status"] == "rejected"
        )

        pending_count = len(pending_requests)

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "⏳ Pending Requests",
            pending_count,
        )

        metric2.metric(
            "✅ Approved Requests",
            approved_count,
        )

        metric3.metric(
            "❌ Rejected Requests",
            rejected_count,
        )

        st.divider()

        st.subheader("⏳ Pending Approval Requests")

        if pending_requests:

            for request in pending_requests:

                request_id = request["request_id"]

                with st.container(border=True):

                    st.markdown(
                        f"### 📋 {request['action']}"
                    )

                    st.write(request["details"])

                    st.caption(
                        f"Request ID: {request_id}"
                    )

                    st.caption(
                        "Created: "
                        + format_timestamp(request["created_at"])
                    )

                    st.warning(
                        "This request is waiting for your decision."
                    )

                    approve_col, reject_col = st.columns(2)

                    with approve_col:

                        if st.button(
                            "✅ Approve",
                            key=f"approve_{request_id}",
                            use_container_width=True,
                            type="primary",
                        ):

                            try:

                                decide_approval(
                                    request_id,
                                    approved=True,
                                )

                                st.success(
                                    "Approval decision saved."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    f"Could not approve request: {error}"
                                )

                    with reject_col:

                        if st.button(
                            "❌ Reject",
                            key=f"reject_{request_id}",
                            use_container_width=True,
                        ):

                            try:

                                decide_approval(
                                    request_id,
                                    approved=False,
                                )

                                st.success(
                                    "Rejection decision saved."
                                )

                                st.rerun()

                            except Exception as error:

                                st.error(
                                    f"Could not reject request: {error}"
                                )

        else:

            st.info(
                "There are no pending approval requests."
            )

        st.divider()

        st.subheader("📚 Approval History")

        status_filter = st.selectbox(
            "Filter by status",
            [
                "All",
                "Pending",
                "Approved",
                "Rejected",
            ],
        )

        filtered_requests = all_requests

        if status_filter != "All":

            filtered_requests = [
                request
                for request in all_requests
                if request["status"] == status_filter.lower()
            ]

        if filtered_requests:

            for request in filtered_requests:

                status = request["status"]

                status_icons = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌",
                }

                with st.expander(
                    f"{status_icons.get(status, '📋')} "
                    f"{request['action']} — {status.upper()}"
                ):

                    st.write(request["details"])

                    st.caption(
                        f"Request ID: {request['request_id']}"
                    )

                    st.caption(
                        "Created: "
                        + format_timestamp(request["created_at"])
                    )

                    st.caption(
                        "Decision date: "
                        + format_timestamp(request["decided_at"])
                    )

        else:

            st.caption(
                "No approval history found for this filter."
            )

        st.divider()

        st.info(
            "Important: Approve and Reject only save a human decision "
            "in the database. They do not publish campaigns, send emails, "
            "or execute any external business action."
        )

    except Exception as error:

        st.error(
            f"Could not load the approval dashboard: {error}"
        )


# =========================================
# ABOUT PAGE
# =========================================

elif st.session_state.page == "About":

    st.title("ℹ️ About AI Marketing Agent")

    st.write(
        """
        AI Marketing Agent is an AI-powered assistant
        designed to help small businesses with marketing.

        Current backend capabilities:

        - AI Marketing Responses
        - Streaming Responses
        - Tool Calling
        - Conversation History
        - Social Media Captions
        - Hashtag Generation
        - Content Planning
        - Image Generation
        - Business Document Search
        - Web Research
        - Conversation Memory
        - Multi-Agent Handoffs
        - Realtime Voice
        - Input Guardrails
        - Human Approval Requests
        - Approval Dashboard
        - Tracing
        """
    )

    st.info(
        "This application is under development. "
        "Additional dashboard features will be connected "
        "in upcoming development steps."
    )