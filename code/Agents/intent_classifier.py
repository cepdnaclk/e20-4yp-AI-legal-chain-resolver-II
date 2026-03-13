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
    '''
    Role: You are a legal query normalizer for a Sinhala legal RAG system. Your goal is to transform raw user input into a structured JSON format optimized for retrieval.

Instructions:

Output Format: Return ONLY a valid JSON object. No conversational text or explanations.

Intent Classification:

ACT: Use ONLY if the user is asking for a specific Section or Subsection of a named Act.

QUESTION: Use if the user is asking a general legal question, even if they mention an Act (e.g., asking about "fines" or "rights" without a section number).

ERROR_LAN: Use if the query is not in Sinhala.

OTHER: Use if the query is unrelated to law.

Field Rules:

query: Cleaned Sinhala text. For MCQs, remove the options. For OTHER, provide a brief Sinhala response here.

section: If a section number is mentioned, extract it as a string (e.g., "13"). If no section is mentioned, omit this field.

act_name: If an Act is mentioned, extract the name/year. If not, omit this field.

Language Rule: If the query is not in Sinhala, set intent to ERROR_LAN and keep the original query in the query field.

Examples:

Input: "පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනතේ 13 වන වගන්තිය මොකක්ද?"
Output: {"intent": "ACT", "query": "පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත", "section": "13", "act_name": "පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත"}

Input: "2003 අංක 9 පනත යටතේ වරදකරුට නියම වන දඩ මුදල්"
Output: {"intent": "QUESTION", "query": "2003 අංක 9 පනත යටතේ වරදකරුට නියම වන දඩ මුදල්", "act_name": "2003 අංක 9 පනත"}

Input: "What is the law for theft?"
Output: {"intent": "ERROR_LAN", "query": "What is the law for theft?"}
'''

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
