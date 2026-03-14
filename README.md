# AI Legal Chain Resolver II

AI Legal Chain Resolver II is a web application that answers Sri Lankan legal queries in Sinhala using a Gemini-backed RAG pipeline. It retrieves relevant legal act sections, generates structured answers, and provides citations with direct PDF downloads for referenced acts.

## Key Features

- Sinhala-first legal Q&A with structured, citation-aware responses.
- Retrieval-augmented generation using act and section context.
- Real-time streaming responses in the UI.
- Citation cards with per-act PDF downloads.

## Architecture Overview

- `code/app.py`: Flask backend serving the UI and API endpoints.
- `code/Agents/*`: Intent classification, retrieval, and response generation logic.
- `code/Tools/*`: Gemini client utilities and retriever helpers.
- `code/static/*`: Frontend UI, streaming display, and citation download flow.
- `code/Data/Acts/*`: Act text and PDF sources used for citations.

## Data Layout

- Act text: `code/Data/Acts/Text/`
- Act PDFs: `code/Data/Acts/PDF/`
- RAG chunks: `code/Data/chunks/`
- Cleaned text: `code/Data/Cleaned/`
- FAISS indexes: `code/Data/Indexes/`

## Folder Structure

```
code/
  Agents/
  Data/
    Acts/
      PDF/
      Text/
    Cleaned/
    Indexes/
  Evaluation/
  Pipelines/
  Tools/
  app.py
```

## Setup

1) Create a `.env` file or export the API key:

```bash
set GEMINI_API_KEY=your_key_here
```

2) Install dependencies:

```bash
pip install -r requirement.txt
```

## How To Run

1) Activate your virtual environment and install dependencies.
2) Run the Flask app:

```bash
python code/app.py
```

Open `http://localhost:5000`.

## How To Add New Data To RAG

1) Put cleaned text files into `code/Data/Cleaned/`.
2) Run `code/Tools/build_faiss.py` to rebuild the FAISS index.

## How To Evaluate

Run the scripts under `code/Evaluation/` for retrieval and QA evaluation.

## API Endpoints

- `POST /api/query`  
  Returns full response JSON with `answer` and `citations`.

- `POST /api/query-stream`  
  Streams the Gemini response as plain text; the UI parses the final JSON.

- `POST /api/citation-pdf`  
  Body: `{ "source": "<source>" }`  
  Downloads `code/Data/Acts/PDF/<source>.pdf` if available.

## Usage Notes

- Citations are grouped by act in the UI; one download button per act.
- Ensure PDF filenames match the `source` field returned by the model.
- Streaming is enabled by default in the UI.

## Tests

Tests and scripts live under `code/Test/` and `code/Tools/`. Run them as needed for your environment.
