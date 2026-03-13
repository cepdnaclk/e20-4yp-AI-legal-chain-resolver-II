import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import retrieve_from_intent  # noqa: E402
from Agents.response_generator import generate_response  # noqa: E402

ANSWER_MARKER = (
    "\u0db1\u0dd2\u0dc0\u0dbb\u0dd0\u0daf\u0dd2 \u0db4\u0dd2\u0dc5\u0dd2\u0dad\u0dd4\u0dbb\u0dd4:"
)
ANSWER_PATTERN = re.compile(
    r"(?i)"
    + re.escape(ANSWER_MARKER)
    + r"\s*([A-D])"
)
LEADING_OPTION_PATTERN = re.compile(r"^\s*([A-D])\b")


def _load_questions(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_query(item: Dict[str, Any]) -> str:
    question_text = item.get("question_text", "").strip()
    options = item.get("options", {}) or {}
    option_lines = []
    for key in ["A", "B", "C", "D"]:
        option = options.get(key, "")
        option_lines.append(f"{key}. {option}")
    return "\n".join([question_text, *option_lines]).strip()


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return _try_parse_json(text[start : end + 1])


def _extract_answer_text(response_text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    trimmed = response_text.strip()
    parsed = _try_parse_json(trimmed)
    if parsed is None:
        parsed = _extract_json_block(trimmed)
    if parsed and "answer" in parsed:
        return str(parsed["answer"]).strip(), parsed
    return trimmed, parsed


def _extract_option_letter(text: str) -> Optional[str]:
    match = ANSWER_PATTERN.search(text)
    if match:
        return match.group(1).upper()
    leading = LEADING_OPTION_PATTERN.search(text)
    if leading:
        return leading.group(1).upper()
    return None


def _update_counts(
    counts: Dict[str, Dict[str, int]], predicted: Optional[str], actual: str
) -> None:
    labels = ["A", "B", "C", "D"]
    for label in labels:
        if label not in counts:
            counts[label] = {"tp": 0, "fp": 0, "fn": 0}
    if predicted is None:
        counts[actual]["fn"] += 1
        return
    if predicted == actual:
        counts[actual]["tp"] += 1
    else:
        counts[predicted]["fp"] += 1
        counts[actual]["fn"] += 1


def _compute_metrics(counts: Dict[str, Dict[str, int]]) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    labels = ["A", "B", "C", "D"]
    precisions = []
    recalls = []
    f1s = []
    for label in labels:
        tp = counts[label]["tp"]
        fp = counts[label]["fp"]
        fn = counts[label]["fn"]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)
        metrics[f"precision_{label}"] = precision
        metrics[f"recall_{label}"] = recall
        metrics[f"f1_{label}"] = f1
    metrics["precision_macro"] = sum(precisions) / len(precisions)
    metrics["recall_macro"] = sum(recalls) / len(recalls)
    metrics["f1_macro"] = sum(f1s) / len(f1s)
    return metrics


def run_evaluation(
    dataset_path: Path,
    rag_enabled: bool,
    top_k: int,
    sleep_s: float,
    output_path: Optional[Path],
) -> None:
    items = _load_questions(dataset_path)
    total = len(items)
    correct = 0
    counts: Dict[str, Dict[str, int]] = {}
    results = []

    for idx, item in enumerate(items, start=1):
        query = _build_query(item)
        test_intent = {"intent": "QUESTION", "query": query}
        chunks = retrieve_from_intent(test_intent, top_k=top_k)
        response = generate_response(query, rag_enabled, chunks)
        answer_text, parsed = _extract_answer_text(response)
        predicted = _extract_option_letter(answer_text)
        actual = str(item.get("correct_option", "")).strip().upper()
        is_correct = predicted == actual
        if is_correct:
            correct += 1
        _update_counts(counts, predicted, actual)

        results.append(
            {
                "question_id": item.get("question_id"),
                "predicted": predicted,
                "actual": actual,
                "correct": is_correct,
                "answer_text": answer_text,
                "raw_response": response,
                "parsed_response": parsed,
            }
        )

        print(
            f"[{idx}/{total}] {item.get('question_id')} -> "
            f"predicted={predicted} actual={actual} correct={is_correct}"
        )

        if sleep_s > 0:
            time.sleep(sleep_s)

    accuracy = correct / total if total else 0.0
    metrics = _compute_metrics(counts)
    metrics["accuracy"] = accuracy

    print("\nOverall metrics:")
    print(f"accuracy: {accuracy:.4f}")
    print(f"precision_macro: {metrics['precision_macro']:.4f}")
    print(f"recall_macro: {metrics['recall_macro']:.4f}")
    print(f"f1_macro: {metrics['f1_macro']:.4f}")

    if output_path:
        output_payload = {"metrics": metrics, "results": results}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(output_payload, handle, ensure_ascii=False, indent=2)
        print(f"\nWrote detailed results to {output_path}")


def main() -> None:
    code_root = Path(__file__).resolve().parents[1]
    default_dataset = (
        code_root / "Data" / "Evaluation" / "consumer_protection_act2003_mcq.json"
    )
    parser = argparse.ArgumentParser(description="Evaluate MCQ accuracy and metrics.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help="Path to MCQ dataset JSON.",
    )
    parser.add_argument(
        "--no-rag",
        action="store_true",
        help="Disable RAG (use model knowledge only).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top-k chunks to retrieve.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.0,
        help="Sleep seconds between requests.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write detailed results JSON.",
    )
    args = parser.parse_args()

    run_evaluation(
        dataset_path=args.dataset,
        rag_enabled=not args.no_rag,
        top_k=args.top_k,
        sleep_s=args.sleep,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
