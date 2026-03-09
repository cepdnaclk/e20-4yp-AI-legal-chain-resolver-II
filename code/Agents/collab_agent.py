from pathlib import Path
import json
import re
import sys
import logging

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import RetrievedChunk, retrieve_from_intent, retrieve_full_section
from Agents.intent_classifier import intent_classify
from Agents.response_generator import generate_response
from Tools.retriever_utils import deduplicate_chunks


def _extract_json_payload(raw: str) -> dict | None:
    cleaned = raw or ""
    fence_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, flags=re.IGNORECASE
    )
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def retrieve_with_intent(user_query: str,RAG_enabled: bool, top_k: int = 5) -> str | None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print("Classifying intent for query: %s", user_query)
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        return None
    print("Intent payload: %s", intent_payload)
    print("==========================\n")
    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    if intent_type == "OTHER" or intent_type.startswith("ERROR"):
        return json.dumps({"answer": intent_payload.get("query")})
    if not RAG_enabled:
        response = generate_response(user_query, RAG_enabled,[])
        return response

    chunks =  retrieve_from_intent(intent_payload, top_k=top_k)
    for idx, chunk in enumerate(chunks, start=1):
        print(
            "Retrieved chunk %s: act=%s, section=%s, source=%s, method=%s",
            idx,
            chunk.act,
            chunk.section_number,
            chunk.source,
            chunk.method,
        )
    print("Generating response with retrieved chunks...")
    response = generate_response(user_query, RAG_enabled, chunks)
    payload = _extract_json_payload(response)
    action = payload.get("action") if payload else None
    if (
        isinstance(action, dict)
        and (action.get("type") or "").upper() == "FETCH_SECTION"
    ):
        act = action.get("act") or intent_payload.get("act")
        section = action.get("section") or intent_payload.get("section")
        extra_chunks = retrieve_full_section(act, section)
        if extra_chunks:
            merged = deduplicate_chunks(extra_chunks + chunks)
            response = generate_response(user_query, RAG_enabled, merged)
    print("Final response:\n", response)
    return response

if __name__ == "__main__":
    query = "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    retrieve_with_intent(query, RAG_enabled=False)

    
