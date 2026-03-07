import argparse
from dataclasses import dataclass
import logging
import math
import os
from pathlib import Path
import re
from typing import List

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def embed_query(self, text):
        return self.model.encode(text).tolist()


@dataclass
class RetrievedChunk:
    content: str
    source: str
    section_number: str | None
    section_title: str | None
    subsection_number: str | None
    act: str | None
    method: str
    score: float | None


def load_vectorstore(repo_root: Path) -> FAISS:
    model_path = repo_root / "Models" / "Embedding" / "sin_bert_finetuned_model"
    index_dir = repo_root / "Data" / "Indexes" / "commercial_law_faiss_index"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not index_dir.exists():
        raise FileNotFoundError(f"FAISS index not found: {index_dir}")

    logging.info("Loading embedding model from %s", model_path)
    model = SentenceTransformer(str(model_path))
    embedding = SentenceTransformerEmbeddings(model)

    logging.info("Loading FAISS index from %s", index_dir)
    return FAISS.load_local(
        str(index_dir),
        embedding,
        allow_dangerous_deserialization=True,
    )


def tokenize(text: str) -> List[str]:
    return re.findall(r"[0-9A-Za-z\u0D80-\u0DFF]+", text)


def retrieve_chunks_faiss(
    vectorstore: FAISS, query: str, top_k: int
) -> List[RetrievedChunk]:
    logging.info("Retrieving top %s chunks for query: %s", top_k, query)
    docs = vectorstore.similarity_search(query=query, k=top_k)
    chunks = []
    for doc in docs:
        metadata = doc.metadata or {}
        source = metadata.get("source", "unknown")
        chunks.append(
            RetrievedChunk(
                content=doc.page_content,
                source=source,
                section_number=metadata.get("section_number"),
                section_title=metadata.get("section_title"),
                subsection_number=metadata.get("subsection_number"),
                act=metadata.get("act"),
                method="faiss",
                score=None,
            )
        )
    return chunks


def retrieve_chunks_bm25(
    vectorstore: FAISS, query: str, top_k: int
) -> List[RetrievedChunk]:
    logging.info("Retrieving top %s BM25 chunks for query: %s", top_k, query)
    doc_ids = list(vectorstore.index_to_docstore_id.values())
    documents = []
    for doc_id in doc_ids:
        doc = vectorstore.docstore.search(doc_id)
        if doc is not None:
            documents.append(doc)

    if not documents:
        return []

    term_frequencies = []
    doc_lengths = []
    document_frequency = {}

    for doc in documents:
        tokens = tokenize(doc.page_content)
        doc_lengths.append(len(tokens))
        counts = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        term_frequencies.append(counts)
        for token in counts:
            document_frequency[token] = document_frequency.get(token, 0) + 1

    avg_doc_length = sum(doc_lengths) / len(doc_lengths)
    k1 = 1.5
    b = 0.75
    query_terms = set(tokenize(query))

    scores = []
    for doc_index, counts in enumerate(term_frequencies):
        score = 0.0
        doc_length = doc_lengths[doc_index]
        for term in query_terms:
            tf = counts.get(term, 0)
            if tf == 0:
                continue
            df = document_frequency.get(term, 0)
            idf = math.log((len(documents) - df + 0.5) / (df + 0.5) + 1)
            denom = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += idf * ((tf * (k1 + 1)) / denom)
        scores.append(score)

    ranked = sorted(
        enumerate(scores),
        key=lambda item: item[1],
        reverse=True,
    )
    chunks = []
    for doc_index, score in ranked[:top_k]:
        doc = documents[doc_index]
        metadata = doc.metadata or {}
        chunks.append(
            RetrievedChunk(
                content=doc.page_content,
                source=metadata.get("source", "unknown"),
                section_number=metadata.get("section_number"),
                section_title=metadata.get("section_title"),
                subsection_number=metadata.get("subsection_number"),
                act=metadata.get("act"),
                method="bm25",
                score=score,
            )
        )
    return chunks


def retrieve_chunks_title(
    vectorstore: FAISS, query: str, top_k: int
) -> List[RetrievedChunk]:
    logging.info("Retrieving top %s title matches for query: %s", top_k, query)
    doc_ids = list(vectorstore.index_to_docstore_id.values())
    documents = []
    for doc_id in doc_ids:
        doc = vectorstore.docstore.search(doc_id)
        if doc is not None:
            documents.append(doc)

    if not documents:
        return []

    query_terms = [term.lower() for term in tokenize(query)]
    scored = []
    for doc in documents:
        metadata = doc.metadata or {}
        title = (metadata.get("section_title") or "").lower()
        if not title:
            scored.append((0, doc))
            continue
        score = 0
        for term in query_terms:
            if term and term in title:
                score += 1
        scored.append((score, doc))

    ranked = sorted(scored, key=lambda item: item[0], reverse=True)
    chunks = []
    for score, doc in ranked[:top_k]:
        metadata = doc.metadata or {}
        chunks.append(
            RetrievedChunk(
                content=doc.page_content,
                source=metadata.get("source", "unknown"),
                section_number=metadata.get("section_number"),
                section_title=metadata.get("section_title"),
                subsection_number=metadata.get("subsection_number"),
                act=metadata.get("act"),
                method="title",
                score=float(score),
            )
        )
    return chunks


def build_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
    logging.info("Building prompt with %s retrieved chunks", len(chunks))
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "[Context {idx} | method: {method} | source: {source} | "
            "section: {section_number} | subsection: {subsection_number} | "
            "title: {section_title}]\n"
            "{content}".format(
                idx=idx,
                method=chunk.method,
                source=chunk.source,
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
        "Use short citations like [source=..., section=..., rule=...].\n\n"
        f"Question:\n{query}\n\n"
        f"Context:\n{context_text}"
    )


def call_gemini(prompt: str, model_name: str) -> str:
    logging.info("Calling Gemini model %s", model_name)
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
    logging.info("Sending prompt to Gemini (chars=%s)", len(prompt))
    response = model.generate_content(prompt)
    if not response or not response.text:
        return "No response text returned from Gemini."
    return response.text.strip()


def parse_args() -> argparse.Namespace:
    query_default = ""
    parser = argparse.ArgumentParser(
        description="Retrieve FAISS chunks and answer with Gemini."
    )
    parser.add_argument("--query", default=query_default, help="User query to answer.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to retrieve.")
    parser.add_argument(
        "--model-name",
        default=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        help="Gemini model name (or set GEMINI_MODEL).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query = "අධිකාරිය පාරිභෝකකියා ආරක්ෂා කරන වගන්තිය කුමක්ද?" if not args.query else args.query
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parents[1]
    logging.info("Repo root: %s", repo_root)
    vectorstore = load_vectorstore(repo_root)
    faiss_chunks = retrieve_chunks_faiss(vectorstore, query, args.top_k)
    bm25_chunks = retrieve_chunks_bm25(vectorstore, query, args.top_k)
    title_chunks = retrieve_chunks_title(vectorstore, query, args.top_k)
    chunks = faiss_chunks + bm25_chunks + title_chunks
    logging.info(
        "Retrieved %s FAISS chunks, %s BM25 chunks, and %s title chunks",
        len(faiss_chunks),
        len(bm25_chunks),
        len(title_chunks),
    )
    print("\nRetrieved chunks:\n")
    for idx, chunk in enumerate(chunks, start=1):
        print(
            "[Chunk {idx} | method: {method} | source: {source} | "
            "section: {section_number} | subsection: {subsection_number} | "
            "title: {section_title}]\n{content}\n".format(
                idx=idx,
                method=chunk.method,
                source=chunk.source,
                section_number=chunk.section_number,
                subsection_number=chunk.subsection_number,
                section_title=chunk.section_title,
                content=chunk.content,
            )
        )
    prompt = build_prompt(query, chunks)
    # answer = call_gemini(prompt, args.model_name)

    # print("\nAnswer:\n")
    # print(answer)


if __name__ == "__main__":
    main()
