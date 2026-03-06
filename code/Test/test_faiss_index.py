from pathlib import Path

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


def main():
    repo_root = Path(__file__).resolve().parents[1]
    model_path = repo_root / "Models" / "Embedding" / "sin_bert_finetuned_model"
    index_dir = repo_root / "Data" / "Indexes" / "bills_of_exchange_2025_index"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    if not index_dir.exists():
        raise FileNotFoundError(f"FAISS index not found: {index_dir}")

    model = SentenceTransformer(str(model_path))
    embedding = SentenceTransformerEmbeddings(model)

    vectorstore = FAISS.load_local(
        str(index_dir),
        embedding,
        allow_dangerous_deserialization=True,
    )

    query = "බැංකුකරු යනු කවුද?"
    results = vectorstore.similarity_search(
        query=query,
        k=5,
    )

    for i, doc in enumerate(results, start=1):
        print(f"\nResult {i}:")
        print(doc.page_content)
        print(doc.metadata)


if __name__ == "__main__":
    main()
