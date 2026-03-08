from pathlib import Path
import json
import sys
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import RetrievedChunk, retrieve_from_intent
from Agents.intent_classifier import intent_classify
from Agents.response_generator import generate_response


def retrieve_with_intent(user_query: str,RAG_enabled: bool, top_k: int = 5) -> str | None:
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        return None
    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    if intent_type == "OTHER" or intent_type.startswith("ERROR"):
        return json.dumps({"answer": intent_payload.get("query")})
    if not RAG_enabled:
        response = generate_response(user_query, RAG_enabled,[])
        return response

    chunks =  retrieve_from_intent(intent_payload, top_k=top_k)
    response = generate_response(user_query, RAG_enabled, chunks)
    print("Final response:\n", response)
    return response

if __name__ == "__main__":
    query = "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    retrieve_with_intent(query, RAG_enabled=False)

    
