from pathlib import Path

from tools.file_search import upload_document, search_documents


BASE_DIR = Path(__file__).resolve().parent

document_path = BASE_DIR / "sample_business.txt"

try:
    print("Uploading Sweet Corner business document...")

    upload_result = upload_document(str(document_path))
    print(upload_result)

    # Extract the vector store ID from the upload result.
    vector_store_id = next(
        line.split(": ", 1)[1]
        for line in upload_result.splitlines()
        if line.startswith("Vector store ID: ")
    )

    print("\nSearching the document...")

    answer = search_documents(
        vector_store_id,
        "What products does Sweet Corner sell, and who is its target audience?",
    )

    print("\n--- SEARCH ANSWER ---")
    print(answer)

except Exception as error:
    print(f"\nTest failed: {type(error).__name__}: {error}")