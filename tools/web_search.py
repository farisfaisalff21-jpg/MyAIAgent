from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from agents import function_tool


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

client = OpenAI()


def search_web(question: str) -> str:
    """Search the web for current marketing information."""

    if not question or not question.strip():
        raise ValueError("Please enter a search question.")

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": "medium",
                }
            ],
            input=(
                "Research this question using web search. "
                "Prefer reliable sources and recent information "
                "for current trends. Include source links when available. "
                "Do not invent facts.\n\n"
                f"Question: {question.strip()}"
            ),
        )

        return response.output_text

    except Exception as error:
        print(
            f"Web search error: {type(error).__name__}: {error}"
        )
        raise RuntimeError(
            "Web search failed. Check the terminal error, "
            "API access, and available API credits."
        ) from error


@function_tool
def search_marketing_web(question: str) -> str:
    """Search the internet for marketing trends and public information."""

    return search_web(question)