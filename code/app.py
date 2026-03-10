import json
import os
import re
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

repo_root = Path(__file__).resolve().parent
sys.path.append(str(repo_root))

from Agents.collab_agent import retrieve_with_intent
from Agents.intent_classifier import preload_gemini
from Tools.retriever_utils import preload_retriever

app = Flask(__name__, template_folder="templates", static_folder="static")
try:
    preload_gemini()
except Exception as exc:
    app.logger.warning("Gemini preload failed: %s", exc)
try:
    repo_root = Path(__file__).resolve().parent
    preload_retriever(repo_root, "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
except Exception as exc:
    app.logger.warning("Retriever preload failed: %s", exc)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    _rag_enabled = bool(payload.get("ragenable"))
    if not query:
        return jsonify({"error": "query_required"}), 400

    try:
        response = retrieve_with_intent(query, RAG_enabled=_rag_enabled)
    except Exception as exc:
        return jsonify({"error": "internal_error", "details": str(exc)}), 500

    raw = response or ""
    cleaned = raw
    fence_match = re.search(
        r"```(?:json)?\s*([\s\S]*?)\s*```", raw, flags=re.IGNORECASE
    )
    if fence_match:
        cleaned = fence_match.group(1).strip()

    parsed = None
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = None

    if parsed and isinstance(parsed, dict):
        return jsonify(
            {
                "answer": parsed.get("answer", ""),
                "citations": parsed.get("citations", []),
            }
        )

    return jsonify({"answer": raw, "citations": []})


@app.route("/api/citation-pdf", methods=["POST"])
def api_citation_pdf():
    payload = request.get_json(silent=True) or {}
    source = (payload.get("source") or "").strip()
    if not source:
        return jsonify({"error": "source_required"}), 400
    if Path(source).name != source:
        return jsonify({"error": "invalid_source"}), 400
    if not re.fullmatch(r"[A-Za-z0-9_\-(). ]+", source):
        return jsonify({"error": "invalid_source"}), 400

    pdf_dir = repo_root / "Data" / "Acts" / "PDF"
    pdf_path = pdf_dir / f"{source}.pdf"
    if not pdf_path.is_file():
        return jsonify({"error": "pdf_not_found"}), 404

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"{source}.pdf",
        mimetype="application/pdf",
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
