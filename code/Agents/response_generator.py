import logging
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Tools.gemini import call_gemini
from Tools.retriever_utils import RetrievedChunk

def build_prompt(query: str, chunks) -> str:

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
        "Return ONLY valid JSON.\n"
        "JSON format:\n"
        "{\n"
        '  "answer": "<clear Sinhala answer>",\n'
        '  "citations": [\n'
        "    {\n"
        '      "source": "<source>",\n'
        '      "act": "<act>",\n'
        '      "section": "<section_number>",\n'
        '      "subsection": "<subsection_number>"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "If you use multiple chunks, include multiple citation objects.\n"
        "Do not add extra text outside JSON.\n\n"
        f"Question:\n{query}\n\n"
        f"Context:\n{context_text}"
    )

def generate_response(query: str, chunks) -> str:
    prompt = build_prompt(query, chunks)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    response = call_gemini(prompt, model_name)
    return response
