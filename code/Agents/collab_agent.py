from typing import List

from retriver import RetrievedChunk, retrieve_from_intent
from intent_classifier import intent_classify
from response_generator import generate_response


def retrieve_with_intent(user_query: str, top_k: int = 5) -> str | None:
    intent_payload = intent_classify(user_query)
    if not intent_payload:
        return None
    chunks =  retrieve_from_intent(intent_payload, top_k=top_k)
    response = generate_response(user_query, chunks)
    print("Final response:\n", response)
    return response

if __name__ == "__main__":
    query = "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    retrieve_with_intent(query)

    