from pathlib import Path
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer
from chunking import iter_sections, build_chunks, DEFAULT_SEPARATORS


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=True).tolist()

    def embed_query(self, text):
        return self.model.encode(text).tolist()


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
ACT_NAME = "2003 අංක 9 දරන පාරිභෝගික කටයුතු පිළිබඳ අධිකාරිය පනත"

def main():
    repo_root = Path(__file__).resolve().parents[1]
    text_file_path = repo_root/"Data/Acts/Cleaned"
    

    files = [f for f in text_file_path.glob("**/*.txt") if f.is_file()]

    for i,file in enumerate(files, start=1):
        print(f"{i}. {file.name}")
    
    choice = int(input("Enter the number of the text file to process: "))
    if choice < 1 or choice > len(files):
        print("Invalid choice. Exiting.")
        return
    selected_file= files[choice - 1].name
    print(f"You selected: {selected_file}")
    text_path = files[choice - 1]
    model_path = repo_root / "Models" / "Embedding" / "sin_bert_finetuned_model"
    output_dir = repo_root / "Data" / "Indexes" / "commercial_law_faiss_index"

    print(output_dir)

    if not text_path.exists():
        raise FileNotFoundError(f"Text file not found: {text_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    print(f"Loading text from {text_path} and model from {model_path}...")
    text = text_path.read_text(encoding="utf-8")

    documents = []
    for section in iter_sections(text):
        chunks = build_chunks(
            section["content"],
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=DEFAULT_SEPARATORS,
        )
        for chunk in chunks:
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "source": text_path.stem,
                        "act": ACT_NAME,
                        "section_number": section["number"],
                        "section_title": section["title"],
                        "subsection_number": section.get("subsection_number"),
                    },
                )
            )
    
    print("Model and text loaded, creating or updating FAISS index...")
    model = SentenceTransformer(str(model_path))
    embedding = SentenceTransformerEmbeddings(model)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        vectorstore = FAISS.load_local(
            str(output_dir),
            embedding,
            allow_dangerous_deserialization=True,
        )
        vectorstore.add_documents(documents)
    else:
        vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=embedding,
        )
    vectorstore.save_local(str(output_dir))

    print(f"Saved FAISS index to {output_dir}")


if __name__ == "__main__":
    main()
