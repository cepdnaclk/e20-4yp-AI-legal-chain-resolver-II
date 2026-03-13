import logging
import os
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Tools.gemini import call_gemini, call_gemini_stream
from Tools.retriever_utils import RetrievedChunk

def build_prompt(query: str, RAG_enabled: bool, chunks) -> str:

    if not RAG_enabled:
        return (
            "You are a legal assistant for Sri lankan LAW. Answer the user question in sinhala based on your knowledge.\n"
            "If you do not know the answer, say you do not have enough information.\n"
            "Return ONLY valid JSON.\n"
            "JSON format:\n"
            "{\n"
            '  "answer": "<clear Sinhala answer>",\n'
            '  "citations": []\n'
            "}\n"
            f"Question:\n{query}"
        )

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
    "You are a legal assistant.\n"
    "Carefully read the user question and the provided context.\n\n"

    "Use the context as the legal source of truth. \n"
    "Do NOT copy the context/Section text directly.\n"
    "Instead understand the legal meaning and produce a clear, well-structured explanation in Sinhala.\n"
    "You may use commonly used English legal terms when helpful, but do NOT introduce any legal facts that are not supported by the context.\n\n"

    "Answer Structure Requirements:\n"
    "1. Start with a direct answer to the question.\n"
    "2. If it is a MCQ, first state \"නිවරැදි පිළිතුර: \" followed by the option letter.\n"
    "3. Then explain the legal rule using numbered sections.\n"
    "4. Use bold words for important legal terms, acts, or concepts.\n"
    "5. When relevant, mention subsection numbers (e.g., (1), (2), (a), (b)).\n"
    "6. Organize the explanation clearly using numbers or sub-points.\n"
    "7. End with a short summary paragraph of the answer.\n\n"

    "Example structure (only as formatting guidance):\n"
    "1. **Main Legal Provision**\n"
    "   Explanation...\n"
    "2. **Conditions or Requirements**\n"
    "   (1) ...\n"
    "   (2) ...\n"
    "3. **Legal Effect**\n"
    "   Explanation...\n\n"

    "Return ONLY valid JSON.\n\n"

    "JSON format:\n"
    "{\n"
    '  "answer": "<structured Sinhala answer with numbered points and bold legal terms, ending with a short summary>",\n'
    '  "citations": [\n'
    "    {\n"
    '      "source": "<source>",\n'
    '      "act": "<act>",\n'
    '      "section": "<section_number>",\n'
    '      "subsection": "<subsection_number>"\n'
    "    }\n"
    "  ],\n"
    "}\n\n"

    "Citation Rules:\n"
    "- Every legal explanation must be supported by the provided context.\n"
    "- If multiple context chunks are used, include multiple citation objects.\n\n"

    "Do NOT include any text outside the JSON structure.\n"
    "Do NOT incode addition field in the JSON other than 'answer' and 'citations'.\n"

    f"Question:\n{query}\n\n"
    f"Context:\n{context_text}"
)

def generate_response(query: str,RAG_enabled: bool, chunks) -> str:
    prompt = build_prompt(query,RAG_enabled, chunks)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    response = call_gemini(prompt, model_name)
    return response


def generate_response_stream(query: str, RAG_enabled: bool, chunks):
    prompt = build_prompt(query, RAG_enabled, chunks)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    return call_gemini_stream(prompt, model_name)
