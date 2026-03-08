import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parents[1]))

def call_gemini(prompt: str, model_name: str) -> str:
    logging.info("Calling Gemini model %s", model_name)
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise ImportError(
            "google-generativeai is not installed. Install it with "
            "`pip install google-generativeai`."
        ) from exc

    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY environment variable.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    logging.info("Sending prompt to Gemini (chars=%s)", len(prompt))
    response = model.generate_content(prompt)
    if not response or not response.text:
        return "No response text returned from Gemini."
    return response.text.strip()
