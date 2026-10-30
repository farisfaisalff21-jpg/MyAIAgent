import os
import re
import sqlite3
from pathlib import Path
from collections.abc import AsyncIterator

from dotenv import load_dotenv
from agents import Runner, SQLiteSession
from openai.types.responses import ResponseTextDeltaEvent

from marketing_agents.marketing_agent import get_marketing_agent


# =========================================
# PATHS AND DATABASES
# =========================================

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = MEMORY_DIR / "conversations.db"
CONVERSATION_INDEX_PATH = MEMORY_DIR / "conversation_index.db"


# =========================================
# CONVERSATION TITLE GENERATOR
# =========================================

def make_conversation_title(message: str) -> str:
    if not isinstance(message, str):
        return "New Conversation"

    title = re.sub(r"\s+", " ", message).strip()

    if not title:
        return "New Conversation"

    first_sentence = re.split(
        r"[.!?\n]", title, maxsplit=1
    )[0]

    if first_sentence.strip():
        title = first_sentence.strip()

    if len(title) > 45:
        shortened = title[:42].rsplit(" ", 1)[0]
        title = shortened + "..." if shortened else title[:42] + "..."

    return title


# =========================================
# CONVERSATION INDEX DATABASE
# =========================================

def initialize_conversation_database() -> None:
    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_hidden INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, session_id)
            )
            """
        )

        columns = connection.execute(
            "PRAGMA table_info(conversations)"
        ).fetchall()

        column_names = {column[1] for column in columns}

        if "is_hidden" not in column_names:
            connection.execute(
                """
                ALTER TABLE conversations
                ADD COLUMN is_hidden INTEGER NOT NULL DEFAULT 0
                """
            )

        connection.commit()


initialize_conversation_database()


# =========================================
# REQUEST VALIDATION
# =========================================

def validate_request(
    user_message: str,
    user_id: str,
    session_id: str,
) -> None:

    if not isinstance(user_message, str) or not user_message.strip():
        raise ValueError("Please enter a marketing request.")

    if len(user_message) > 5000:
        raise ValueError(
            "Please keep your request under 5000 characters."
        )

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    if len(user_id) > 100:
        raise ValueError("User ID is too long.")

    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    if len(session_id) > 100:
        raise ValueError("Session ID is too long.")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OpenAI API key is not configured.")


# =========================================
# CREATE SESSION
# =========================================

def create_session(
    user_id: str,
    session_id: str,
) -> SQLiteSession:

    combined_session_id = (
        f"{user_id.strip()}:{session_id.strip()}"
    )

    return SQLiteSession(
        combined_session_id,
        str(DATABASE_PATH),
    )


# =========================================
# SAVE CONVERSATION
# =========================================

def save_conversation(
    user_id: str,
    session_id: str,
    title: str,
) -> None:

    safe_title = make_conversation_title(title)

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO conversations
            (user_id, session_id, title)
            VALUES (?, ?, ?)
            """,
            (
                user_id.strip(),
                session_id.strip(),
                safe_title,
            ),
        )

        connection.commit()


# =========================================
# LIST ACTIVE CONVERSATIONS
# =========================================

def list_conversations(user_id: str) -> list[dict]:

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT session_id, title, created_at
            FROM conversations
            WHERE user_id = ?
              AND is_hidden = 0
            ORDER BY created_at DESC
            """,
            (user_id.strip(),),
        ).fetchall()

    return [dict(row) for row in rows]


# =========================================
# LIST HIDDEN CONVERSATIONS
# =========================================

def list_hidden_conversations(user_id: str) -> list[dict]:

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT session_id, title, created_at
            FROM conversations
            WHERE user_id = ?
              AND is_hidden = 1
            ORDER BY created_at DESC
            """,
            (user_id.strip(),),
        ).fetchall()

    return [dict(row) for row in rows]


# =========================================
# HIDE CONVERSATION
# =========================================

def hide_conversation(user_id: str, session_id: str) -> bool:

    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE conversations
            SET is_hidden = 1
            WHERE user_id = ?
              AND session_id = ?
            """,
            (user_id.strip(), session_id.strip()),
        )

        connection.commit()
        return cursor.rowcount > 0


# =========================================
# RESTORE CONVERSATION
# =========================================

def restore_conversation(user_id: str, session_id: str) -> bool:

    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE conversations
            SET is_hidden = 0
            WHERE user_id = ?
              AND session_id = ?
            """,
            (user_id.strip(), session_id.strip()),
        )

        connection.commit()
        return cursor.rowcount > 0


# =========================================
# RENAME CONVERSATION
# =========================================

def rename_conversation(
    user_id: str,
    session_id: str,
    new_title: str,
) -> bool:

    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    if not isinstance(new_title, str) or not new_title.strip():
        raise ValueError("Conversation title cannot be empty.")

    safe_title = re.sub(
        r"\s+", " ", new_title
    ).strip()[:80]

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        cursor = connection.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE user_id = ?
              AND session_id = ?
            """,
            (
                safe_title,
                user_id.strip(),
                session_id.strip(),
            ),
        )

        connection.commit()
        return cursor.rowcount > 0


# =========================================
# SEARCH CONVERSATIONS
# =========================================

def search_conversations(
    user_id: str,
    query: str,
    include_hidden: bool = False,
) -> list[dict]:

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    safe_query = query.strip()

    if not safe_query:
        if include_hidden:
            return list_hidden_conversations(user_id)

        return list_conversations(user_id)

    pattern = f"%{safe_query}%"

    hidden_filter = "" if include_hidden else "AND is_hidden = 0"

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            f"""
            SELECT session_id, title, created_at
            FROM conversations
            WHERE user_id = ?
              {hidden_filter}
              AND title LIKE ?
            ORDER BY created_at DESC
            """,
            (user_id.strip(), pattern),
        ).fetchall()

    return [dict(row) for row in rows]


# =========================================
# GET CONVERSATION HISTORY
# =========================================

async def get_conversation_history(
    user_id: str,
    session_id: str,
) -> list:

    if not user_id or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    if not session_id or not session_id.strip():
        raise ValueError("Session ID cannot be empty.")

    session = create_session(user_id, session_id)

    return await session.get_items()


# =========================================
# CONVERSATION ANALYTICS
# =========================================

def get_conversation_analytics(user_id: str) -> dict:
    """Return real conversation analytics for one user."""

    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("User ID cannot be empty.")

    initialize_conversation_database()

    with sqlite3.connect(CONVERSATION_INDEX_PATH) as connection:
        connection.row_factory = sqlite3.Row

        daily_rows = connection.execute(
            """
            SELECT
                DATE(created_at) AS day,
                COUNT(*) AS total,
                SUM(
                    CASE WHEN is_hidden = 0 THEN 1 ELSE 0 END
                ) AS visible,
                SUM(
                    CASE WHEN is_hidden = 1 THEN 1 ELSE 0 END
                ) AS hidden
            FROM conversations
            WHERE user_id = ?
            GROUP BY DATE(created_at)
            ORDER BY day
            """,
            (user_id.strip(),),
        ).fetchall()

        totals_row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(
                    SUM(CASE WHEN is_hidden = 0 THEN 1 ELSE 0 END),
                    0
                ) AS visible,
                COALESCE(
                    SUM(CASE WHEN is_hidden = 1 THEN 1 ELSE 0 END),
                    0
                ) AS hidden
            FROM conversations
            WHERE user_id = ?
            """,
            (user_id.strip(),),
        ).fetchone()

    return {
        "daily": [dict(row) for row in daily_rows],
        "totals": dict(totals_row),
    }


# =========================================
# NORMAL MARKETING RESPONSE
# =========================================

async def generate_marketing_response(
    user_message: str,
    session_id: str = "default",
    user_id: str = "default_user",
) -> str:

    validate_request(user_message, user_id, session_id)

    try:
        save_conversation(user_id, session_id, user_message)

        agent = get_marketing_agent()
        session = create_session(user_id, session_id)

        result = await Runner.run(
            agent,
            user_message.strip(),
            session=session,
        )

        return result.final_output

    except ValueError:
        raise

    except Exception as error:
        print(
            f"Marketing agent error: "
            f"{type(error).__name__}: {error}"
        )

        raise RuntimeError(
            "Sorry, the marketing request failed. "
            "Please check your API credits and internet "
            "connection, then try again."
        ) from error


# =========================================
# STREAMING MARKETING RESPONSE
# =========================================

async def stream_marketing_response(
    user_message: str,
    session_id: str = "default",
    user_id: str = "default_user",
) -> AsyncIterator[str]:

    validate_request(user_message, user_id, session_id)

    try:
        save_conversation(user_id, session_id, user_message)

        agent = get_marketing_agent()
        session = create_session(user_id, session_id)

        result = Runner.run_streamed(
            agent,
            user_message.strip(),
            session=session,
        )

        async for event in result.stream_events():
            if (
                event.type == "raw_response_event"
                and isinstance(
                    event.data,
                    ResponseTextDeltaEvent,
                )
            ):
                yield event.data.delta

    except ValueError:
        raise

    except Exception as error:
        print(
            f"Marketing streaming error: "
            f"{type(error).__name__}: {error}"
        )

        raise RuntimeError(
            "Sorry, the streaming request failed. "
            "Please check your API credits and internet "
            "connection, then try again."
        ) from error