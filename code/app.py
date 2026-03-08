import json
import os
import re
import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

repo_root = Path(__file__).resolve().parent
sys.path.append(str(repo_root))

from Agents.collab_agent import retrieve_with_intent

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/query", methods=["POST"])
def api_query():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query_required"}), 400

    try:
        response = retrieve_with_intent(query)
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
