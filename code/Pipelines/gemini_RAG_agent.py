import argparse
from dataclasses import dataclass
import logging
import os
from pathlib import Path
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
    section_header: str | None


def load_vectorstore(repo_root: Path) -> FAISS:
    model_path = repo_root / "Models" / "Embedding" / "sin_bert_finetuned_model"
    index_dir = repo_root / "Data" / "Indexes" / "bills_of_exchange_2025_index"

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


def retrieve_chunks(vectorstore: FAISS, query: str, top_k: int) -> List[RetrievedChunk]:
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
                section_header=metadata.get("section_header"),
            )
        )
    return chunks


def build_prompt(query: str, chunks: List[RetrievedChunk]) -> str:
    logging.info("Building prompt with %s retrieved chunks", len(chunks))
    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            "[Context {idx} | source: {source} | "
            "section: {section_number} | title: {section_title} | header: {section_header}]\n"
            "{content}".format(
                idx=idx,
                source=chunk.source,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                section_header=chunk.section_header,
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
    query = "අණකරුගේ ගිණුමේ මුදල් ප්‍රමාණවත් නොවීම හේතුවෙන් නොගෙවා ආපසු එවන ලද චෙක්පතක් සම්බන්ධයෙන්, ආදායකයා හෝ යථා කාල ධාරකයා විසින් නීති කෘත්‍යයක් ආරම්භ කළ හැකි කාලසීමාව කුමක්ද?"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parents[1]
    logging.info("Repo root: %s", repo_root)
    vectorstore = load_vectorstore(repo_root)
    chunks = retrieve_chunks(vectorstore, query, args.top_k)
    logging.info("Retrieved %s chunks", len(chunks))
    print("\nRetrieved chunks:\n")
    for idx, chunk in enumerate(chunks, start=1):
        print(
            "[Chunk {idx} | source: {source} | section: {section_number} | "
            "title: {section_title} | header: {section_header}]\n{content}\n".format(
                idx=idx,
                source=chunk.source,
                section_number=chunk.section_number,
                section_title=chunk.section_title,
                section_header=chunk.section_header,
                content=chunk.content,
            )
        )
    prompt = build_prompt(query, chunks)
    answer = call_gemini(prompt, args.model_name)

    print("\nAnswer:\n")
    print(answer)


if __name__ == "__main__":
    main()
