from datetime import datetime, timezone
from pathlib import Path
import json
import re
import sys
import logging
import time

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import retrieve_from_intent, retrieve_full_section
from Agents.intent_classifier import intent_classify
from Agents.response_generator import generate_response, generate_response_stream
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


def _write_retrieval_log(
    retrieve_time_seconds: float | None,
    answer_time_seconds: float | None,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    log_dir = repo_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "retrieval_log.jsonl"
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieve_time_ms": round(retrieve_time_seconds * 1000, 2)
        if retrieve_time_seconds is not None
        else None,
        "answer_time_ms": round(answer_time_seconds * 1000, 2)
        if answer_time_seconds is not None
        else None,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def retrieve_with_intent(user_query: str,RAG_enabled: bool=True, top_k: int = 5) -> str | None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    print(user_query)
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        _write_retrieval_log(None, None)
        return None
    print("Intent payload: %s", intent_payload)
    print("==========================\n")
    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    if intent_type == "OTHER" or intent_type.startswith("ERROR"):
        response = json.dumps({"answer": intent_payload.get("query")})
        _write_retrieval_log(None, None)
        return response
    if not RAG_enabled:
        answer_start = time.perf_counter()
        response = generate_response(user_query, RAG_enabled,[])
        answer_time_seconds = time.perf_counter() - answer_start
        _write_retrieval_log(None, answer_time_seconds)
        return response

    retrieve_start = time.perf_counter()
    chunks, all_chunks = retrieve_from_intent(
        intent_payload, top_k=top_k, return_all=True
    )
    retrieve_time_seconds = time.perf_counter() - retrieve_start
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
    answer_start = time.perf_counter()
    response = generate_response(user_query, RAG_enabled, chunks)
    answer_time_seconds = time.perf_counter() - answer_start
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
            answer_start = time.perf_counter()
            response = generate_response(user_query, RAG_enabled, merged)
            answer_time_seconds = time.perf_counter() - answer_start
    print("Final response:\n", response)
    _write_retrieval_log(retrieve_time_seconds, answer_time_seconds)
    return response


def retrieve_with_intent_stream(user_query: str, RAG_enabled: bool, top_k: int = 5):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        yield json.dumps({"answer": "No response generated.", "citations": []})
        return

    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    if intent_type == "OTHER" or intent_type.startswith("ERROR"):
        yield json.dumps({"answer": intent_payload.get("query"), "citations": []})
        return

    if not RAG_enabled:
        yield from generate_response_stream(user_query, RAG_enabled, [])
        return

    chunks = retrieve_from_intent(intent_payload, top_k=top_k)
    yield from generate_response_stream(user_query, RAG_enabled, chunks)

if __name__ == "__main__":
    query = "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    retrieve_with_intent(query, RAG_enabled=False)

    
