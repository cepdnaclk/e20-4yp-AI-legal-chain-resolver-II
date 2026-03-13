import logging
import os
from pathlib import Path
import sys
from typing import List

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Tools.retriever_utils import (
    RetrievedChunk,
    deduplicate_chunks,
    get_vectorstore,
    retrieve_chunks_by_act_section,
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

def retrieve_from_intent(
    intent_payload: dict, top_k: int = 5, return_all: bool = False
) -> List[RetrievedChunk] | tuple[List[RetrievedChunk], List[RetrievedChunk]]:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parents[1]
    logging.info("Repo root: %s", repo_root)
    vectorstore, _embedding_model = get_vectorstore(repo_root)

    intent_type = (intent_payload.get("type") or intent_payload.get("intent") or "").upper()
    query = intent_payload.get("query") or intent_payload.get("quesry") or ""
    act = intent_payload.get("act")
    section = intent_payload.get("section")

    if intent_type == "ACT":
        if not section:
            return ([], []) if return_all else []
        chunks = retrieve_chunks_by_section(vectorstore, str(section))
        return (chunks, chunks) if return_all else chunks

    if not query:
        return ([], []) if return_all else []

    faiss_chunks = retrieve_chunks_faiss(vectorstore, query, top_k)
    bm25_chunks = retrieve_chunks_bm25(vectorstore, query, top_k)
    title_chunks = retrieve_chunks_title(vectorstore, act, section)
    all_chunks = faiss_chunks + bm25_chunks + title_chunks
    unique_chunks = deduplicate_chunks(all_chunks)
    reranked_chunks = rerank_chunks(
        query,
        unique_chunks,
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        top_k=3,
    )
    reranked_chunks = _expand_top_section(vectorstore, reranked_chunks, act)
    logging.info(
        "Retrieved %s FAISS chunks, %s BM25 chunks, and %s title chunks",
        len(faiss_chunks),
        len(bm25_chunks),
        len(title_chunks),
    )
    logging.info(
        "Deduplicated chunks: %s -> %s", len(all_chunks), len(unique_chunks)
    )
    if return_all:
        return reranked_chunks, all_chunks
    return reranked_chunks


def retrieve_full_section(
    act: str | None, section: str | None
) -> List[RetrievedChunk]:
    if not section:
        return []
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parents[1]
    vectorstore, _embedding_model = get_vectorstore(repo_root)
    if act:
        return retrieve_chunks_by_act_section(vectorstore, act, section)
    return retrieve_chunks_by_section(vectorstore, str(section))


def _expand_top_section(
    vectorstore, chunks: List[RetrievedChunk], intent_act: str | None
) -> List[RetrievedChunk]:
    if not chunks:
        return chunks
    top = chunks[0]
    if top.method in {"act_section", "section"}:
        return chunks
    if not top.section_number:
        return chunks

    act = top.act or intent_act
    if act:
        expanded = retrieve_chunks_by_act_section(
            vectorstore, act, top.section_number
        )
    else:
        expanded = retrieve_chunks_by_section(vectorstore, str(top.section_number))

    if not expanded:
        return chunks

    filtered = []
    for chunk in chunks:
        if chunk.section_number == top.section_number and (
            not act or chunk.act == act
        ):
            continue
        filtered.append(chunk)
    return expanded + filtered

if __name__ == "__main__":
    # query ='''
    # පාරිභෝගික කටයුතු අධිකාරීයේ ප්‍රධාන අරමුණක් 
    # නොවන්නේ කුමක්ද? 
    # A. වයවසායන් අතර සීමාකාරී වෙළඳ ගිවිසුම් පාලනය කිරීම 
    # B. ත්‍රඟකාරීත්වයට අහිතකර භාවිත්‍යන් විමර්ශනය කිරීම 
    # C. පාරිභෝගිකයන්ට අසාධාරණ මිල ගණන් නියම කිරීමට වයවසායන්ට ඉඩ දීම
    # D. භාණ්ඩ හා සේවා වල මිල, ගුණාත්මකභාවය සහ ලබා ගැනීම පිළිබඳව පාරිමභෝගිකයන් දැනුවත් කිරීම    
    # '''
    # query = '''
    # අධිකාරිය විසින් පාරිභෝගිකයා ආරක්ෂා කිරීම සඳහා කුමන කරුණු සම්බන්ධයෙන් සාමාන්‍ය විධාන නිකුත් කළ හැකිද?
    # A. භාණ්ඩ ආනයනය කිරීම පමණක්
    # B. භාණ්ඩ ලේබල් කිරීම, මිල ලකුණු කිරීම, ඇසිරීම සහ විකිණීම
    # C. භාණ්ඩ ප්‍රවාහනය කිරීම පමණක්
    # D. වෙළෙඳසැල් ලියාපදිංචි කිරීම
    # '''
    # query= "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    query="භාණ්ඩ සඟවා තබා ගැනීම හෝ රැස්කර තබා ගැනීම වරදක්ද?"
    
    test_intent = {
        "intent": "QUESTION",
        "query": query
    }
    query= "අධිකාරියේ සහාපතිවරයා සභ සාමාජිකයන්‌ගේ ධුර කාලය කුමක්ද?"
    query2 = "පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනතේ 13 වන වගන්තිය මොකක්ද?"
    query3 = "අධිකාරියේ අරමුණු මොනවාද?"
    query4="අධිකාරියේ කර්තවය"
    query5="වෙළෙන්දකුට හාණ්ඩ විකිණීම ප්‍රනික්ෂේප කළ"

    retrieved_chunks = retrieve_from_intent(test_intent, top_k=5)
    for chunk in retrieved_chunks:
        print(f"Method: {chunk.method}, Source: {chunk.source}, Act: {chunk.act}, "
              f"Section: {chunk.section_number}, Subsection: {chunk.subsection_number}, "
              f"Title: {chunk.section_title}\nContent: {chunk.content}\n{'-'*80}")
