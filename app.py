import asyncio
import os
import uuid
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from marketing_agents.service import (
    stream_marketing_response,
    list_conversations,
    list_hidden_conversations,
    get_conversation_history,
    hide_conversation,
    restore_conversation,
    rename_conversation,
    get_conversation_analytics,
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
# CUSTOM CSS
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
        color: white;
        font-size: 17px;
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
# PATHS AND USER ID
# =========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

os.makedirs(MEMORY_DIR, exist_ok=True)

USER_ID_FILE = os.path.join(
    MEMORY_DIR,
    "user_id.txt"
)


def load_or_create_user_id():

    if os.path.exists(USER_ID_FILE):

        with open(
            USER_ID_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            saved_user_id = file.read().strip()

        if saved_user_id:
            return saved_user_id

    new_user_id = f"user_{uuid.uuid4().hex[:10]}"

    with open(
        USER_ID_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(new_user_id)

    return new_user_id


# =========================================
# CONVERSATION HELPERS
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

            messages.append({
                "role": role,
                "content": text_content,
            })

    return messages


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
        if search_text in conversation.get(
            "title", ""
        ).lower()
    ]


def format_timestamp(timestamp):

    if not timestamp:
        return "Not available"

    return str(timestamp).replace(
        "T", " "
    ).split(".")[0]


# =========================================
# APPROVAL ANALYTICS HELPERS
# =========================================

def get_approval_dataframe(requests):

    rows = []

    for request in requests:

        created_at = pd.to_datetime(
            request.get("created_at"),
            errors="coerce",
            utc=True,
        )

        decided_at = pd.to_datetime(
            request.get("decided_at"),
            errors="coerce",
            utc=True,
        )

        rows.append({
            "request_id": request.get(
                "request_id", ""
            ),
            "action": request.get(
                "action", "Unknown"
            ),
            "status": request.get(
                "status", "unknown"
            ),
            "created_at": created_at,
            "decided_at": decided_at,
        })

    return pd.DataFrame(
        rows,
        columns=[
            "request_id",
            "action",
            "status",
            "created_at",
            "decided_at",
        ],
    )


def filter_approval_dataframe(
    df,
    start_date,
    end_date
):

    if df.empty:
        return df.copy()

    result = df.copy()

    result["created_day"] = (
        result["created_at"].dt.date
    )

    result = result[
        (result["created_day"] >= start_date)
        & (result["created_day"] <= end_date)
    ]

    return result.copy()


# =========================================
# WEEKLY AND MONTHLY REPORT HELPER
# =========================================

def make_period_report(
    df,
    date_column,
    period,
    count_column=None,
):

    if df.empty:

        return pd.DataFrame(
            columns=["period", "count"]
        )

    result = df.copy()

    result[date_column] = pd.to_datetime(
        result[date_column],
        errors="coerce",
    )

    result = result.dropna(
        subset=[date_column]
    )

    if result.empty:

        return pd.DataFrame(
            columns=["period", "count"]
        )

    dates = result[date_column]

    # Handle both timezone-aware and timezone-naive dates.

    if dates.dt.tz is not None:

        dates = dates.dt.tz_convert(None)

    result["period"] = (
        dates.dt.to_period(period).astype(str)
    )

    if (
        count_column is not None
        and count_column in result.columns
    ):

        report = (
            result.groupby("period")[count_column]
            .sum()
            .reset_index(name="count")
        )

    else:

        report = (
            result.groupby("period")
            .size()
            .reset_index(name="count")
        )

    return report.sort_values("period")


# =========================================
# CSV DOWNLOAD HELPER
# =========================================

def csv_download_button(
    label,
    dataframe,
    filename,
    key,
):

    csv_data = dataframe.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=key,
        use_container_width=True,
    )


# =========================================
# SESSION STATE
# =========================================

if "user_id" not in st.session_state:

    st.session_state.user_id = (
        load_or_create_user_id()
    )


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

    st.caption(
        "Your intelligent marketing assistant"
    )

    st.divider()

    st.subheader("Navigation")

    pages = [
        "Dashboard",
        "AI Marketing Chat",
        "Human Approval",
        "Analytics Dashboard",
        "About",
    ]

    selected_page = st.radio(
        "Select Page",
        pages,
        index=pages.index(
            st.session_state.page
        ),
        format_func=lambda page: (
            "🤝 Human Approval"
            if page == "Human Approval"
            else "📈 Analytics Dashboard"
            if page == "Analytics Dashboard"
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

        conversations = list_conversations(
            user_id
        )

        filtered_conversations = filter_conversations(
            conversations,
            search_text,
        )

        st.caption("📂 Previous Conversations")

        if filtered_conversations:

            for conversation in filtered_conversations:

                conversation_id = conversation[
                    "session_id"
                ]

                conversation_title = conversation[
                    "title"
                ]

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

                    open_conversation(
                        conversation_id
                    )

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

                        rename_submitted = (
                            st.form_submit_button(
                                "✏️ Rename Conversation",
                                use_container_width=True,
                            )
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

                st.caption(
                    "No matching conversations found."
                )

            else:

                st.caption(
                    "No previous conversations yet."
                )

        # HIDDEN CHATS

        st.divider()

        with st.expander(
            "🙈 Hidden Chats",
            expanded=False,
        ):

            hidden_conversations = (
                list_hidden_conversations(user_id)
            )

            filtered_hidden = filter_conversations(
                hidden_conversations,
                search_text,
            )

            if filtered_hidden:

                for conversation in filtered_hidden:

                    hidden_id = conversation[
                        "session_id"
                    ]

                    hidden_title = conversation[
                        "title"
                    ]

                    st.write(
                        f"📦 {hidden_title[:35]}"
                    )

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

                                st.success(
                                    "Conversation restored!"
                                )

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

                st.caption(
                    "No hidden conversations."
                )

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

    st.caption(
        "AI Marketing Agent | Development Version"
    )


# =========================================
# MAIN DASHBOARD
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
            1
            for item in dashboard_all_approvals
            if item["status"] == "approved"
        )

    except Exception as error:

        dashboard_conversations = []
        dashboard_hidden = []
        dashboard_pending = []
        approved_total = 0

        st.warning(
            f"Some dashboard statistics could not load: {error}"
        )

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
            "Find information in uploaded business documents.",
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

            feature_name, feature_description = (
                features[feature_index]
            )

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

    st.markdown(
        '<div class="section-heading">🚀 Quick Actions</div>',
        unsafe_allow_html=True,
    )

    action_col1, action_col2, action_col3, action_col4 = st.columns(4)

    with action_col1:

        if st.button(
            "💬 Open AI Chat",
            use_container_width=True,
            type="primary",
        ):

            st.session_state.page = "AI Marketing Chat"
            st.rerun()

    with action_col2:

        if st.button(
            "🤝 Human Approval",
            use_container_width=True,
        ):

            st.session_state.page = "Human Approval"
            st.rerun()

    with action_col3:

        if st.button(
            "📈 Analytics",
            use_container_width=True,
        ):

            st.session_state.page = "Analytics Dashboard"
            st.rerun()

    with action_col4:

        if st.button(
            "ℹ️ About Project",
            use_container_width=True,
        ):

            st.session_state.page = "About"
            st.rerun()

    st.divider()

    st.caption(
        "AI Marketing Agent | Intelligent Marketing Workspace"
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

        st.session_state.messages.append({
            "role": "user",
            "content": user_prompt,
        })

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

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                })

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
        "Review proposed business actions before any external action."
    )

    try:

        pending_requests = list_pending_requests()

        all_requests = list_all_requests()

        approved_count = sum(
            1
            for request in all_requests
            if request["status"] == "approved"
        )

        rejected_count = sum(
            1
            for request in all_requests
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
                        + format_timestamp(
                            request["created_at"]
                        )
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
                        + format_timestamp(
                            request["created_at"]
                        )
                    )

                    st.caption(
                        "Decision date: "
                        + format_timestamp(
                            request["decided_at"]
                        )
                    )

        else:

            st.caption(
                "No approval history found for this filter."
            )

        st.divider()

        st.info(
            "Approve and Reject save a human decision in the database. "
            "They do not publish campaigns, send emails, or execute "
            "external business actions."
        )

    except Exception as error:

        st.error(
            f"Could not load the approval dashboard: {error}"
        )


# =========================================
# ANALYTICS DASHBOARD
# =========================================

elif st.session_state.page == "Analytics Dashboard":

    st.title("📈 Analytics Dashboard")

    st.caption(
        "Monitor conversation activity and human approval trends."
    )

    st.divider()

    # DATE RANGE FILTER

    today = date.today()

    default_start = today - timedelta(days=29)

    selected_dates = st.date_input(
        "📅 Select Analytics Date Range",
        value=(default_start, today),
        max_value=today,
        key="analytics_date_range",
    )

    if isinstance(selected_dates, (tuple, list)):

        if len(selected_dates) == 2:

            start_date, end_date = selected_dates

        elif len(selected_dates) == 1:

            start_date = selected_dates[0]
            end_date = selected_dates[0]

        else:

            start_date = default_start
            end_date = today

    else:

        start_date = selected_dates
        end_date = selected_dates

    if start_date > end_date:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()

    st.caption(
        f"Showing analytics from {start_date} to {end_date}"
    )

    st.divider()

    # -------------------------------------
    # CONVERSATION ANALYTICS
    # -------------------------------------

    st.subheader("💬 Conversation Analytics")

    conversation_df = pd.DataFrame(
        columns=[
            "day",
            "total",
            "visible",
            "hidden",
        ]
    )

    try:

        conversation_analytics = get_conversation_analytics(
            st.session_state.user_id
        )

        daily_records = conversation_analytics.get(
            "daily",
            [],
        )

        conversation_df = pd.DataFrame(
            daily_records,
            columns=[
                "day",
                "total",
                "visible",
                "hidden",
            ],
        )

        if not conversation_df.empty:

            conversation_df["day"] = pd.to_datetime(
                conversation_df["day"],
                errors="coerce",
            ).dt.date

            conversation_df = conversation_df.dropna(
                subset=["day"]
            )

            conversation_df = conversation_df[
                (conversation_df["day"] >= start_date)
                & (conversation_df["day"] <= end_date)
            ].copy()

        total_conversations = (
            int(conversation_df["total"].sum())
            if not conversation_df.empty else 0
        )

        visible_conversations = (
            int(conversation_df["visible"].sum())
            if not conversation_df.empty else 0
        )

        hidden_conversations = (
            int(conversation_df["hidden"].sum())
            if not conversation_df.empty else 0
        )

        conv_col1, conv_col2, conv_col3 = st.columns(3)

        conv_col1.metric(
            "Total Conversations",
            total_conversations,
        )

        conv_col2.metric(
            "Visible Conversations",
            visible_conversations,
        )

        conv_col3.metric(
            "Hidden Conversations",
            hidden_conversations,
        )

        st.markdown("#### 📊 Daily Conversations")

        if not conversation_df.empty:

            daily_chart = conversation_df.set_index(
                "day"
            )[["total"]]

            st.line_chart(
                daily_chart,
                use_container_width=True,
            )

            st.markdown("#### 👁️ Visible vs Hidden")

            visibility_chart = conversation_df.set_index(
                "day"
            )[["visible", "hidden"]]

            st.bar_chart(
                visibility_chart,
                use_container_width=True,
            )

            with st.expander(
                "View conversation data"
            ):

                st.dataframe(
                    conversation_df,
                    use_container_width=True,
                    hide_index=True,
                )

        else:

            st.info(
                "No conversations were found in this date range."
            )

        csv_download_button(
            "⬇️ Download Conversation Analytics CSV",
            conversation_df,
            "conversation_analytics.csv",
            "conversation_csv",
        )

    except Exception as error:

        st.error(
            f"Could not load conversation analytics: {error}"
        )

    st.divider()

    # -------------------------------------
    # APPROVAL ANALYTICS
    # -------------------------------------

    st.subheader("🤝 Human Approval Analytics")

    st.caption(
        "Approval analytics include all records in the approvals database. "
        "The current approval database does not store a user ID."
    )

    approval_df = pd.DataFrame(
        columns=[
            "request_id",
            "action",
            "status",
            "created_at",
            "decided_at",
        ]
    )

    try:

        all_approval_records = list_all_requests()

        full_approval_df = get_approval_dataframe(
            all_approval_records
        )

        approval_df = filter_approval_dataframe(
            full_approval_df,
            start_date,
            end_date,
        )

        pending_total = int(
            (approval_df["status"] == "pending").sum()
        )

        approved_total = int(
            (approval_df["status"] == "approved").sum()
        )

        rejected_total = int(
            (approval_df["status"] == "rejected").sum()
        )

        approval_col1, approval_col2, approval_col3 = st.columns(3)

        approval_col1.metric(
            "⏳ Pending",
            pending_total,
        )

        approval_col2.metric(
            "✅ Approved",
            approved_total,
        )

        approval_col3.metric(
            "❌ Rejected",
            rejected_total,
        )

        # APPROVAL SUCCESS RATE

        decided_total = (
            approved_total + rejected_total
        )

        success_rate = (
            (approved_total / decided_total) * 100
            if decided_total > 0 else 0.0
        )

        st.markdown("#### 🎯 Approval Success Rate")

        rate_col1, rate_col2 = st.columns(2)

        rate_col1.metric(
            "Approval Rate",
            f"{success_rate:.1f}%",
        )

        rate_col2.metric(
            "Total Decided Requests",
            decided_total,
        )

        if decided_total > 0:

            st.progress(
                success_rate / 100,
                text=(
                    f"{success_rate:.1f}% of decided "
                    "requests approved"
                ),
            )

        else:

            st.info(
                "No approval decisions are available "
                "for calculating the success rate."
            )

        st.caption(
            "Approval Rate = Approved ÷ (Approved + Rejected) × 100. "
            "Pending requests are excluded."
        )

        # APPROVAL STATUS CHART

        st.markdown(
            "#### 📊 Approval Status Distribution"
        )

        status_chart = pd.DataFrame(
            {
                "Requests": [
                    pending_total,
                    approved_total,
                    rejected_total,
                ]
            },
            index=[
                "Pending",
                "Approved",
                "Rejected",
            ],
        )

        if int(status_chart["Requests"].sum()) > 0:

            st.bar_chart(
                status_chart,
                use_container_width=True,
            )

        else:

            st.info(
                "No approval requests were found in this date range."
            )

        # DAILY APPROVALS

        st.markdown(
            "#### 📅 Daily Approval Requests"
        )

        if not approval_df.empty:

            approval_df["created_day"] = (
                approval_df["created_at"].dt.date
            )

            daily_approvals = (
                approval_df
                .groupby(["created_day", "status"])
                .size()
                .unstack(fill_value=0)
            )

            for status in [
                "pending",
                "approved",
                "rejected",
            ]:

                if status not in daily_approvals.columns:
                    daily_approvals[status] = 0

            daily_approvals = daily_approvals[
                [
                    "pending",
                    "approved",
                    "rejected",
                ]
            ].sort_index()

            st.bar_chart(
                daily_approvals,
                use_container_width=True,
            )

            # DECISIONS OVER TIME

            st.markdown(
                "#### ✅ Decisions Over Time"
            )

            decisions_df = approval_df[
                approval_df["decided_at"].notna()
            ].copy()

            decisions_df = decisions_df[
                decisions_df["status"].isin(
                    ["approved", "rejected"]
                )
            ]

            if not decisions_df.empty:

                decisions_df["decision_day"] = (
                    decisions_df["decided_at"].dt.date
                )

                decisions_df = decisions_df[
                    (
                        decisions_df["decision_day"]
                        >= start_date
                    )
                    &
                    (
                        decisions_df["decision_day"]
                        <= end_date
                    )
                ]

                if not decisions_df.empty:

                    decision_chart = (
                        decisions_df
                        .groupby(
                            ["decision_day", "status"]
                        )
                        .size()
                        .unstack(fill_value=0)
                    )

                    for status in [
                        "approved",
                        "rejected",
                    ]:

                        if status not in decision_chart.columns:
                            decision_chart[status] = 0

                    decision_chart = decision_chart[
                        ["approved", "rejected"]
                    ]

                    st.line_chart(
                        decision_chart,
                        use_container_width=True,
                    )

                else:

                    st.info(
                        "No decisions were recorded during this date range."
                    )

            else:

                st.info(
                    "No decisions have been recorded yet."
                )

        else:

            st.info(
                "No approval records are available for this date range."
            )

        with st.expander(
            "View approval records"
        ):

            st.dataframe(
                approval_df[
                    [
                        "request_id",
                        "action",
                        "status",
                        "created_at",
                        "decided_at",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

        csv_download_button(
            "⬇️ Download Approval Analytics CSV",
            approval_df,
            "approval_analytics.csv",
            "approval_csv",
        )

    except Exception as error:

        st.error(
            f"Could not load approval analytics: {error}"
        )

    # -------------------------------------
    # WEEKLY REPORTS
    # -------------------------------------

    st.divider()

    st.subheader("📅 Weekly Reports")

    try:

        weekly_conversations = conversation_df.copy()

        if not weekly_conversations.empty:

            weekly_conversations["report_date"] = (
                pd.to_datetime(
                    weekly_conversations["day"],
                    errors="coerce",
                )
            )

        weekly_conversations_report = make_period_report(
            weekly_conversations,
            "report_date",
            "W",
            count_column="total",
        )

        weekly_approvals_report = make_period_report(
            approval_df,
            "created_at",
            "W",
        )

        weekly_col1, weekly_col2 = st.columns(2)

        with weekly_col1:

            st.markdown(
                "#### Conversations per Week"
            )

            if not weekly_conversations_report.empty:

                st.bar_chart(
                    weekly_conversations_report.set_index(
                        "period"
                    ),
                    use_container_width=True,
                )

                csv_download_button(
                    "⬇️ Download Weekly Conversations",
                    weekly_conversations_report,
                    "weekly_conversations.csv",
                    "weekly_conversations_csv",
                )

            else:

                st.info(
                    "No weekly conversation data available."
                )

        with weekly_col2:

            st.markdown(
                "#### Approval Requests per Week"
            )

            if not weekly_approvals_report.empty:

                st.bar_chart(
                    weekly_approvals_report.set_index(
                        "period"
                    ),
                    use_container_width=True,
                )

                csv_download_button(
                    "⬇️ Download Weekly Approvals",
                    weekly_approvals_report,
                    "weekly_approvals.csv",
                    "weekly_approvals_csv",
                )

            else:

                st.info(
                    "No weekly approval data available."
                )

    except Exception as error:

        st.error(
            f"Could not generate weekly reports: {error}"
        )

    # -------------------------------------
    # MONTHLY REPORTS
    # -------------------------------------

    st.divider()

    st.subheader("🗓️ Monthly Reports")

    try:

        monthly_conversations = conversation_df.copy()

        if not monthly_conversations.empty:

            monthly_conversations["report_date"] = (
                pd.to_datetime(
                    monthly_conversations["day"],
                    errors="coerce",
                )
            )

        monthly_conversations_report = make_period_report(
            monthly_conversations,
            "report_date",
            "M",
            count_column="total",
        )

        monthly_approvals_report = make_period_report(
            approval_df,
            "created_at",
            "M",
        )

        monthly_col1, monthly_col2 = st.columns(2)

        with monthly_col1:

            st.markdown(
                "#### Conversations per Month"
            )

            if not monthly_conversations_report.empty:

                st.bar_chart(
                    monthly_conversations_report.set_index(
                        "period"
                    ),
                    use_container_width=True,
                )

                csv_download_button(
                    "⬇️ Download Monthly Conversations",
                    monthly_conversations_report,
                    "monthly_conversations.csv",
                    "monthly_conversations_csv",
                )

            else:

                st.info(
                    "No monthly conversation data available."
                )

        with monthly_col2:

            st.markdown(
                "#### Approval Requests per Month"
            )

            if not monthly_approvals_report.empty:

                st.bar_chart(
                    monthly_approvals_report.set_index(
                        "period"
                    ),
                    use_container_width=True,
                )

                csv_download_button(
                    "⬇️ Download Monthly Approvals",
                    monthly_approvals_report,
                    "monthly_approvals.csv",
                    "monthly_approvals_csv",
                )

            else:

                st.info(
                    "No monthly approval data available."
                )

    except Exception as error:

        st.error(
            f"Could not generate monthly reports: {error}"
        )

    st.divider()

    st.caption(
        "Analytics Dashboard | Local SQLite Database"
    )


# =========================================
# ABOUT PAGE
# =========================================

elif st.session_state.page == "About":

    st.title("ℹ️ About AI Marketing Agent")

    st.markdown(
        """
        ## 🚀 AI Marketing Agent

        AI Marketing Agent is an AI-powered assistant
        designed to help businesses with marketing.

        ### Main Capabilities

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
        - Conversation Analytics
        - Approval Analytics
        - CSV Export
        - Weekly Reports
        - Monthly Reports
        - Approval Success Rate
        - Agent Tracing

        ### Technology

        - Python
        - OpenAI Agents SDK
        - Streamlit
        - SQLite
        - Pandas
        """
    )

    st.divider()

    st.info(
        "AI Marketing Agent is under development."
    )

    st.caption(
        "AI Marketing Agent | Development Version"
    )