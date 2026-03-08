import json
import os

from dotenv import load_dotenv


SYSTEM_PROMPT = (
    "You are a legal query normalizer for a Sinhala legal RAG system. "
    "Given a Sinhala user query, return a JSON object with intent and a "
    "cleaned query for retrieval. "
    "Rules: "
    "1) Output ONLY valid JSON. "
    "2) intent must be one of: QUESTION, ACT, SECTION, OTHER. "
    "3) query should be a short Sinhala noun phrase without a trailing question. "
    "4) If a specific act is mentioned, include act field. "
    "5) If a section number is mentioned, include section as a number string. "
    "6) If no act/section is present, omit those fields. "
    "7) Remove filler words and keep legal terms. "
    "8) Do not add extra text outside JSON. "
    "9)If the query is not in Sinhala, return intent as ERROR_LAN and keep the original query."
    "10) If the query is unrelated to law, return intent as OTHER and give respsnose as you normally do in sinhla."
    "Examples: "
    "Input: \"විකුණනු බඩුවක් ප්‍රමිතියෙන් තොර නම් ගත හැකි පියවර මොනවාද?\" "
    "Output: {\"intent\":\"QUESTION\",\"query\":\"විකුණනු ලබන භාණ්ඩයක් ප්‍රමිතියෙන් තොර\"} "
    "Input: \"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනතේ 13 වන වගන්තිය මොකක්ද?\" "
    "Output: {\"intent\":\"ACT\",\"query\":\"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත\",\"section\":\"13\"}"
)


def call_gemini(prompt: str, model_name: str) -> str:
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
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    if not response or not response.text:
        return ""
    return response.text.strip()


def build_prompt(user_query: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "User query:\n"
        f"{user_query}\n\n"
        "Return JSON now."
    )


def intent_classify(user_query: str) -> None:
    if not user_query:
        print("No query provided.")
        return

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    prompt = build_prompt(user_query)
    raw = call_gemini(prompt, model_name)
    if not raw:
        print("No response from Gemini.")
        return

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return

    return parsed


if __name__ == "__main__":
    query = "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    result = intent_classify(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
