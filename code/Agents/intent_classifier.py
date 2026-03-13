import json
import os

from dotenv import load_dotenv

try:
    import google.genai as genai
    from google.genai import types
except ImportError as exc:
    raise ImportError(
        "google-genai is not installed. Install it with "
        "`pip install google-genai`."
    ) from exc


SYSTEM_PROMPT = (
    "You are a legal query normalizer for a Sinhala legal RAG system. "
    "Given a Sinhala user query, return a JSON object with intent and a "
    "cleaned query for retrieval. "
    "Rules: "
    "1) Output ONLY valid JSON. "
    "2) intent must be one of: QUESTION, ACT, ERROR_LAN, OTHER. "
    "3) query should be a short Sinhala noun phrase without a trailing question. "
    "4) If a specific act is mentioned, include act field. "
    "5) If query is MCQ question keep query as it is without any changes."
    "6) If a section number is mentioned, include section as a number string. "
    "7) If no act/section is present, omit those fields. "
    "8) Remove filler words and keep legal terms. "
    "9) If query is containing question about \"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරියේ\", make it  \"අධිකාරියේ\" by remove the word පාරිභෝගික කටයුතු පිළිබඳ and keep rest as it is. "
    "10) Do not add extra text outside JSON. "
    "11)If the query is not in Sinhala, return intent as ERROR_LAN and keep the original query."
    "12) If the query is unrelated to law, return intent as OTHER and give respsnose as you normally do in sinhla,in query field."
    "Examples: "
    "Input: \"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරියේ කාර්‍ය්ය/කර්තවය මොනවාද?\" "
    "Output: {\"intent\":\"QUESTION\",\"query\":\"අධිකාරියේ කර්තවය\"} "
    "Input: \"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනතේ 13 වන වගන්තිය මොකක්ද?\" "
    "Output: {\"intent\":\"ACT\",\"query\":\"පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත\",\"section\":\"13\"}"
)


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


def preload_gemini() -> None:
    get_gemini_client()


def call_gemini(prompt: str, model_name: str) -> str:
    client = get_gemini_client()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
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
    query = "පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය කාර්‍ය මොනවාද"
    query='''
පාරිමභෝගික කටයුතු අධිකාරී පනත් ප්‍රධාන අරමුණක් නොවන කුමක්ද? 
    A. වයවසායන් අත්‍ර සීමාකාරී මවළඳ ගිවිසුම් පාලනය කිරීම 
    B. ත්‍රඟකාරීත්වයට අිත්‍කර භාවිත්‍යන් විමශජනය කිරීම 
    C. පාරිමභෝගිකයන්ට අසාධාරණ මිල ගණන් නියම කිරීමට වයවසායන්ට ඉඩ ීම 
    D. භාණ්ඩ හා මස්වා වල මිල, ගුණාත්මකභාවය සහ ලබා ගැනීම පිළිබඳව පාරිමභෝගිකයන් දැනුවත් කිරීම  '''
    result = intent_classify(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
