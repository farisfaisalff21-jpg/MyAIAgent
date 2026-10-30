from tools.web_search import search_web


def main():
    question = (
        "What are three current social media marketing trends "
        "for small bakery businesses in 2026? Include source links."
    )

    print("Testing Web Search...\n")

    try:
        result = search_web(question)
        print("--- WEB SEARCH RESULTS ---")
        print(result)

    except Exception as error:
        print(f"Test failed: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()