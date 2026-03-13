import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
PIPELINES_DIR = REPO_ROOT / "Pipelines"
sys.path.append(str(PIPELINES_DIR))
sys.path.append(str(REPO_ROOT))

from Tools.chunking import iter_sections, build_chunks, DEFAULT_SEPARATORS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chunk a text file using the shared chunking module."
    )
    parser.add_argument(
        "--input",
        default="Data/Acts/Text/Consumer_Affairs_Authority_ActNo9_of_2003.txt",
        help="Relative path to the input text file.",
    )
    parser.add_argument(
        "--output",
        default="Data/chunks/chunks.txt",
        help="Relative path to write the chunk output.",
    )
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = REPO_ROOT / args.input
    output_path = REPO_ROOT / args.output

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    text = input_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        chunk_index = 0
        for section in iter_sections(text):
            chunks = build_chunks(
                section["content"],
                chunk_size=args.chunk_size,
                chunk_overlap=args.chunk_overlap,
                separators=DEFAULT_SEPARATORS,
            )
            for chunk in chunks:
                chunk_index += 1
                handle.write(
                    "--- chunk {idx} (len={length}) | "
                    "section={section_number} | subsection={subsection_number} | "
                    "title={section_title} ---\n".format(
                        idx=chunk_index,
                        length=len(chunk),
                        section_number=section["number"],
                        subsection_number=section.get("subsection_number"),
                        section_title=section["title"],
                    )
                )
                handle.write(chunk.strip() + "\n\n")

    print(f"Wrote {chunk_index} chunks to {output_path}")


if __name__ == "__main__":
    main()
