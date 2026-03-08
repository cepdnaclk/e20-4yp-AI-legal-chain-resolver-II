import logging
import os
from pathlib import Path
import sys
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Tools.retriever_utils import (
    RetrievedChunk,
    deduplicate_chunks,
    load_vectorstore,
    retrieve_chunks_bm25,
    retrieve_chunks_by_section,
    retrieve_chunks_faiss,
    retrieve_chunks_title,
    rerank_chunks,
)

def build_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
    logging.info("Building prompt with %s retrieved chunks", len(chunks))
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "[Context {idx} | method: {method} | source: {source} | act: {act} | "
            "section: {section_number} | subsection: {subsection_number} | "
            "title: {section_title}]\n"
            "{content}".format(
                idx=idx,
                method=chunk.method,
                source=chunk.source,
                act=chunk.act,
                section_number=chunk.section_number,
                subsection_number=chunk.subsection_number,
                section_title=chunk.section_title,
                content=chunk.content,
            )
        )

    context_text = "\n\n".join(context_blocks)
    return (
        "You are a legal assistant. Answer the user question using only the context.\n"
        "If the context is insufficient, say you do not have enough information.\n"
        "When you use a chunk, cite it by its source/section metadata if provided.\n"
        "There might be multiple relevant chunks; you can use information from all of them, but dont use unrelated chunks. \n"
        "At the end, provide summary of the answer in one short paragraph. \n"
        "Use short citations like [source=..., section=..., rule=...].\n\n"
        f"Question:\n{query}\n\n"
        f"Context:\n{context_text}"
    )

def retrieve_from_intent(intent_payload: dict, top_k: int = 5) -> List[RetrievedChunk]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parents[1]
    logging.info("Repo root: %s", repo_root)
    vectorstore, _embedding_model = load_vectorstore(repo_root)

    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    query = intent_payload.get("query") or intent_payload.get("quesry") or ""
    act = intent_payload.get("act")
    section = intent_payload.get("section")

    if intent_type == "ACT":
        if not section:
            return []
        return retrieve_chunks_by_section(vectorstore, str(section))

    if not query:
        return []

    faiss_chunks = retrieve_chunks_faiss(vectorstore, query, top_k)
    bm25_chunks = retrieve_chunks_bm25(vectorstore, query, top_k)
    title_chunks = retrieve_chunks_title(vectorstore, act, section)
    chunks = faiss_chunks + bm25_chunks + title_chunks
    unique_chunks = deduplicate_chunks(chunks)
    reranked_chunks = rerank_chunks(
        query,
        unique_chunks,
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        top_k,
    )
    logging.info(
        "Retrieved %s FAISS chunks, %s BM25 chunks, and %s title chunks",
        len(faiss_chunks),
        len(bm25_chunks),
        len(title_chunks),
    )
    logging.info("Deduplicated chunks: %s -> %s", len(chunks), len(unique_chunks))
    return reranked_chunks
