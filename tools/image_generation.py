import base64
import re
from pathlib import Path

from dotenv import load_dotenv
from agents import function_tool
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "generated_images"


def create_marketing_image(
    prompt: str,
    filename: str = "marketing_image",
) -> str:
    """Generate a marketing image and save it locally."""

    if not prompt.strip():
        return "Error: Please provide an image description."

    safe_filename = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        filename,
    ).strip("_")[:60] or "marketing_image"

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        client = OpenAI()

        result = client.images.generate(
            model="gpt-image-2",
            prompt=prompt.strip(),
            size="1024x1024",
            quality="low",
            n=1,
        )

        if not result.data or not result.data[0].b64_json:
            return "Error: The image API returned no image."

        image_bytes = base64.b64decode(result.data[0].b64_json)
        output_path = OUTPUT_DIR / f"{safe_filename}.png"
        output_path.write_bytes(image_bytes)

        return f"Image generated successfully. Saved to: {output_path}"

    except Exception as error:
        print(f"Image generation error: {type(error).__name__}: {error}")
        return "Image generation failed. Check the terminal error, API credits, and model access."


@function_tool
def generate_marketing_image(
    prompt: str,
    filename: str = "marketing_image",
) -> str:
    """Generate a promotional image for a business."""

    return create_marketing_image(prompt, filename) 