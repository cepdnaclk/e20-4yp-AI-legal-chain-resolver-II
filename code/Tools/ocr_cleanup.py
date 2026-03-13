from pathlib import Path


OCR_CORRECTIONS = {
    "අධීකෟරිය": "අධිකාරිය",
    "වගන්නිය": "වගන්තිය",
    "හාණ්ඩ": "භාණ්ඩ",
}


def correct_words(text: str) -> str:
    for wrong, correct in OCR_CORRECTIONS.items():
        text = text.replace(wrong, correct)
    return text


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    input_dir = repo_root / "Data" / "Acts" / "Text"
    output_dir = repo_root / "Data" / "Acts" / "Clean"

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    files = sorted([f for f in input_dir.glob("**/*.txt") if f.is_file()])
    if not files:
        print(f"No .txt files found in {input_dir}")
        return

    for i, file in enumerate(files, start=1):
        print(f"{i}. {file.name}")

    choice = int(input("Enter the number of the text file to clean: "))
    if choice < 1 or choice > len(files):
        print("Invalid choice. Exiting.")
        return

    selected_file = files[choice - 1]
    print(f"You selected: {selected_file.name}")

    raw_text = selected_file.read_text(encoding="utf-8")
    cleaned_text = correct_words(raw_text)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / selected_file.name
    output_path.write_text(cleaned_text, encoding="utf-8")

    print(f"Wrote cleaned file to {output_path}")


if __name__ == "__main__":
    main()
