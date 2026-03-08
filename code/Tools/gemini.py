import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import google.genai as genai
except ImportError as exc:
    raise ImportError(
        "google-genai is not installed. Install it with "
        "`pip install google-genai`."
    ) from exc

_GENAI_CLIENT = None


def get_gemini_client():
    global _GENAI_CLIENT
    if _GENAI_CLIENT:
        return _GENAI_CLIENT

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY environment variable.")

    _GENAI_CLIENT = genai.Client(api_key=api_key)
    return _GENAI_CLIENT


def call_gemini(prompt: str, model_name: str) -> str:
    logging.info("Calling Gemini model %s", model_name)
    client = get_gemini_client()
    logging.info("Sending prompt to Gemini (chars=%s)", len(prompt))
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    if not response or not response.text:
        return "No response text returned from Gemini."
    return response.text.strip()
