import sqlite3
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

from agents import function_tool


BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "memory"
DB_PATH = DB_DIR / "approvals.db"


def get_connection():
    """Create a connection to the approval database."""

    DB_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the approval table if it does not exist."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS approval_requests (
                request_id TEXT PRIMARY KEY,
                action TEXT NOT NULL,
                details TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (
                        status IN (
                            'pending',
                            'approved',
                            'rejected'
                        )
                    ),
                created_at TEXT NOT NULL,
                decided_at TEXT
            )
            """
        )


def create_approval_request(
    action: str,
    details: str,
) -> dict:
    """Save a proposed action for human review."""

    action = action.strip()
    details = details.strip()

    if not action:
        raise ValueError("Action cannot be empty.")

    if not details:
        raise ValueError("Action details cannot be empty.")

    initialize_database()

    request = {
        "request_id": str(uuid4()),
        "action": action,
        "details": details,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO approval_requests (
                request_id,
                action,
                details,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                request["request_id"],
                request["action"],
                request["details"],
                request["status"],
                request["created_at"],
            ),
        )

    return request


def get_approval_request(request_id: str):
    """Retrieve an approval request using its ID."""

    initialize_database()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM approval_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    return dict(row) if row else None


def list_pending_requests() -> list[dict]:
    """List all requests awaiting a human decision."""

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM approval_requests
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def list_all_requests() -> list[dict]:
    """List all approval requests, including completed decisions."""

    initialize_database()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM approval_requests
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def decide_approval(
    request_id: str,
    approved: bool,
) -> dict:
    """Record a human decision without executing the proposed action."""

    if not isinstance(approved, bool):
        raise ValueError(
            "Approval decision must be True or False."
        )

    initialize_database()

    status = "approved" if approved else "rejected"
    decided_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE approval_requests
            SET status = ?, decided_at = ?
            WHERE request_id = ?
              AND status = 'pending'
            """,
            (status, decided_at, request_id),
        )

        if cursor.rowcount != 1:
            raise ValueError(
                "Request not found or it has already been decided."
            )

    result = get_approval_request(request_id)

    if result is None:
        raise RuntimeError(
            "Could not retrieve the updated request."
        )

    return result


@function_tool
def request_human_approval(
    action: str,
    details: str,
) -> str:
    """Create a pending approval request for a proposed business action."""

    try:
        request = create_approval_request(
            action,
            details,
        )

        return (
            "Approval request created successfully.\n"
            f"Request ID: {request['request_id']}\n"
            f"Action: {request['action']}\n"
            f"Details: {request['details']}\n"
            f"Status: {request['status']}\n"
            "A human must review this request separately. "
            "No external action has been executed."
        )

    except (ValueError, sqlite3.Error) as error:
        return (
            f"Could not create approval request: {error}"
        )


if __name__ == "__main__":

    request = create_approval_request(
        action="Publish marketing campaign",
        details="Proposed Sweet Corner Instagram campaign.",
    )

    print("Approval request saved:")
    print(f"ID: {request['request_id']}")
    print(f"Action: {request['action']}")
    print(f"Status: {request['status']}")
    print(f"Database: {DB_PATH}")
    print("No external action was executed.")