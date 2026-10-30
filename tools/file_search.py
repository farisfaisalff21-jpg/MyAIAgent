import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from agents import function_tool


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

client = OpenAI()


def upload_document(file_path: str) -> str:
    """Upload a document and wait until it is searchable."""

    path = Path(file_path).resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    supported_extensions = {
        ".pdf", ".txt", ".md", ".docx",
        ".json", ".py", ".html", ".csv",
    }

    if path.suffix.lower() not in supported_extensions:
        raise ValueError(
            "Unsupported file type. Try PDF, TXT, MD, or DOCX."
        )

    vector_store = client.vector_stores.create(
        name=f"Marketing Documents - {path.stem}"
    )

    try:
        with path.open("rb") as document:
            result = client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store.id,
                file=document,
            )

        if result.status != "completed":
            error = getattr(result, "last_error", None)
            raise RuntimeError(
                f"Document indexing failed: "
                f"{error or result.status}"
            )

        return (
            "Document is ready for search!\n"
            f"Filename: {path.name}\n"
            f"Vector store ID: {vector_store.id}\n"
            f"File ID: {result.id}\n"
            "Save the Vector store ID to search this document later."
        )

    except Exception:
        client.vector_stores.delete(vector_store.id)
        raise


def search_documents(
    vector_store_id: str,
    question: str,
) -> str:
    """Search uploaded documents and answer a question."""

    if not vector_store_id.strip():
        raise ValueError("Vector store ID cannot be empty.")

    if not question.strip():
        raise ValueError("Please enter a search question.")

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=(
            "Answer using the uploaded business documents. "
            "If the documents do not contain the answer, say so. "
            "Do not invent business facts.\n"
            f"Question: {question.strip()}"
        ),
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id.strip()],
            }
        ],
    )

    return response.output_text


@function_tool
def search_business_documents(question: str) -> str:
    """Search configured business documents for relevant information."""

    vector_store_id = os.getenv(
        "OPENAI_VECTOR_STORE_ID", ""
    ).strip()

    if not vector_store_id:
        return (
            "File Search is not configured. "
            "Set OPENAI_VECTOR_STORE_ID in your .env file."
        )

    try:
        return search_documents(vector_store_id, question)

    except Exception as error:
        print(
            f"Business document search error: "
            f"{type(error).__name__}: {error}"
        )
        return (
            "Document search failed. "
            "Check the terminal error and API configuration."
        )