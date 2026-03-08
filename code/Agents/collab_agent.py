from typing import List

from retriver import RetrievedChunk, retrieve_from_intent
from intent_classifier import intent_classify


def retrieve_with_intent(user_query: str, top_k: int = 5) -> List[RetrievedChunk]:
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        return []
    return retrieve_from_intent(intent_payload, top_k=top_k)
