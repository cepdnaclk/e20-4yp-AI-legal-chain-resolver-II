import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zipfile import ZipFile
import xml.etree.ElementTree as ET

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Agents.retriver import retrieve_from_intent  # noqa: E402


def _load_shared_strings(zip_file: ZipFile) -> List[str]:
    try:
        data = zip_file.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(data)
    texts: List[str] = []
    for si in root.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
        parts = []
        for t in si.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"):
            if t.text:
                parts.append(t.text)
        texts.append("".join(parts))
    return texts


def _get_sheet_xml(zip_file: ZipFile, sheet_path: str) -> bytes:
    return zip_file.read(sheet_path)


def _parse_sheet(
    sheet_xml: bytes, shared_strings: List[str]
) -> List[List[Optional[str]]]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(sheet_xml)
    rows: List[List[Optional[str]]] = []
    for row in root.findall(".//x:row", ns):
        row_values: List[Optional[str]] = []
        for cell in row.findall("x:c", ns):
            cell_type = cell.attrib.get("t")
            value_elem = cell.find("x:v", ns)
            if value_elem is None:
                inline = cell.find("x:is/x:t", ns)
                row_values.append(inline.text if inline is not None else None)
                continue
            raw_value = value_elem.text or ""
            if cell_type == "s":
                try:
                    row_values.append(shared_strings[int(raw_value)])
                except (ValueError, IndexError):
                    row_values.append(None)
            else:
                row_values.append(raw_value)
        rows.append(row_values)
    return rows


def _load_xlsx_rows(path: Path) -> List[Dict[str, Any]]:
    with ZipFile(path) as zip_file:
        shared_strings = _load_shared_strings(zip_file)
        sheet_xml = _get_sheet_xml(zip_file, "xl/worksheets/sheet1.xml")
        rows = _parse_sheet(sheet_xml, shared_strings)

    if not rows:
        return []
    header = [cell.strip() if isinstance(cell, str) else "" for cell in rows[0]]
    records: List[Dict[str, Any]] = []
    for row in rows[1:]:
        if not any(cell for cell in row):
            continue
        record = {}
        for idx, key in enumerate(header):
            if not key:
                continue
            value = row[idx] if idx < len(row) else None
            record[key] = value
        records.append(record)
    return records


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
    records: Iterable[Dict[str, Any]], top_k: int
) -> Tuple[Dict[str, float], List[Dict[str, Any]]]:
    total = 0
    hits = 0
    mrr_total = 0.0
    precision_sum = 0.0
    recall_sum = 0.0
    details: List[Dict[str, Any]] = []

    for record in records:
        question = (record.get("Question") or "").strip()
        relevant_section = _normalize_section(record.get("Relevant Section"))
        if not question or not relevant_section:
            continue
        total += 1

        test_intent = {"intent": "QUESTION", "query": question}
        chunks = retrieve_from_intent(test_intent, top_k=top_k)
        retrieved_sections = [_normalize_section(chunk.section_number) for chunk in chunks]

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
                "question": question,
                "relevant_section": relevant_section,
                "retrieved_sections": retrieved_sections,
                "hit": hit,
                "hit_rank": hit_rank,
            }
        )

    if total == 0:
        return {"hit_rate": 0.0, "precision_at_k": 0.0, "recall_at_k": 0.0, "mrr": 0.0}, []

    metrics = {
        "hit_rate": hits / total,
        "precision_at_k": precision_sum / total,
        "recall_at_k": recall_sum / total,
        "mrr": mrr_total / total,
    }
    return metrics, details


def main() -> None:
    code_root = Path(__file__).resolve().parents[1]
    default_dataset = code_root / "Data" / "Evaluation" / "consumer_act2003.xlsx"
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality for short answers.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=default_dataset,
        help="Path to the XLSX dataset.",
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
        default=code_root /"Evaluation" / "Results" / "consumer_act2003_results.json",
        help="Optional path to write detailed results JSON.",
    )
    args = parser.parse_args()

    records = _load_xlsx_rows(args.dataset)
    metrics, details = _evaluate_retrieval(records, args.top_k)

    print("Retrieval metrics:")
    print(f"hit_rate@{args.top_k}: {metrics['hit_rate']:.4f}")
    print(f"precision@{args.top_k}: {metrics['precision_at_k']:.4f}")
    print(f"recall@{args.top_k}: {metrics['recall_at_k']:.4f}")
    print(f"mrr@{args.top_k}: {metrics['mrr']:.4f}")

    if args.output:
        payload = {"metrics": metrics, "details": details}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        print(f"\nWrote detailed results to {args.output}")


if __name__ == "__main__":
    main()
