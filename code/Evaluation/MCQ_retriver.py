import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import retrieve_from_intent  # noqa: E402


def _load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_section(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"(\d+[A-Za-z]?)", text)
    if match:
        return match.group(1)
    return text


def _evaluate_retrieval(
    items: Iterable[Dict[str, Any]], top_k: int
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    total = 0
    hits = 0
    mrr_total = 0.0
    precision_sum = 0.0
    recall_sum = 0.0
    details: List[Dict[str, Any]] = []

    for item in items:
        question = (item.get("question_text") or "").strip()
        relevant_section = _normalize_section(item.get("section"))
        if not question or not relevant_section:
            continue
        total += 1

        test_intent = {"intent": "QUESTION", "query": question}
        chunks = retrieve_from_intent(test_intent, top_k=top_k)
        retrieved_sections = [
            _normalize_section(chunk.section_number) for chunk in chunks
        ]

        hit_rank = None
        for idx, section in enumerate(retrieved_sections, start=1):
            if section == relevant_section:
                hit_rank = idx
                break

        hit = hit_rank is not None
        if hit:
            hits += 1
            mrr_total += 1.0 / hit_rank

        precision_at_k = 1.0 / top_k if hit else 0.0
        recall_at_k = 1.0 if hit else 0.0
        precision_sum += precision_at_k
        recall_sum += recall_at_k

        details.append(
            {
                "question_id": item.get("question_id"),
                "question": question,
                "relevant_section": relevant_section,
                "retrieved_sections": retrieved_sections,
                "hit": hit,
                "hit_rank": hit_rank,
            }
        )

    if total == 0:
        return {
            "hit_rate": 0.0,
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
        }, []

    metrics = {
        "hit_rate": hits / total,
        "precision_at_k": precision_sum / total,
        "recall_at_k": recall_sum / total,
        "mrr": mrr_total / total,
    }
    return metrics, details


def main() -> None:
    code_root = Path(__file__).resolve().parents[1]
    default_dataset = (
        code_root
        / "Data"
        / "Evaluation"
        / "consumer_protection_act2003_mcq.json"
    )
    results_dir = code_root / "Evaluation" / "Results"
    default_output = results_dir / "mcq_retrieval_results.json"

    parser = argparse.ArgumentParser(
        description="Evaluate MCQ retrieval quality using section matching."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help="Path to MCQ JSON dataset.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Top-k chunks to retrieve.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Output path for detailed results JSON.",
    )
    args = parser.parse_args()

    items = _load_questions(args.dataset)
    metrics, details = _evaluate_retrieval(items, args.top_k)

    print("Retrieval metrics:")
    print(f"hit_rate@{args.top_k}: {metrics['hit_rate']:.4f}")
    print(f"precision@{args.top_k}: {metrics['precision_at_k']:.4f}")
    print(f"recall@{args.top_k}: {metrics['recall_at_k']:.4f}")
    print(f"mrr@{args.top_k}: {metrics['mrr']:.4f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"metrics": metrics, "details": details}
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"\nWrote detailed results to {args.output}")


if __name__ == "__main__":
    main()
