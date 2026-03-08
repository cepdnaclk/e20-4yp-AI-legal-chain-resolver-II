import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_SEPARATORS = ["\n\n", "\n", ".", " ", ""]
SECTION_PATTERN = re.compile(
    r"^\s*(?P<num>\d+)\.\s*(?P<title>[^\n]{0,200})",
    flags=re.MULTILINE,
)
SUBSECTION_PATTERN = re.compile(
    r"^\s*\((?P<num>[0-9]+)\)\s*",
    flags=re.MULTILINE | re.ASCII,
)


def iter_sections(text):
    matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        yield {
            "number": None,
            "title": None,
            "subsection_number": None,
            "content": text,
        }
        return

    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group("title").strip()
        subsection_in_title = SUBSECTION_PATTERN.match(title)
        if subsection_in_title:
            title = title[subsection_in_title.end():].strip()
        number = match.group("num").strip()
        content = text[start:end].strip()
        subsections = list(SUBSECTION_PATTERN.finditer(content))
        if not subsections:
            yield {
                "number": number,
                "title": title,
                "subsection_number": None,
                "content": content,
            }
            continue

        prefix = content[:subsections[0].start()].strip()
        if prefix and prefix not in {number, f"{number}."}:
            yield {
                "number": number,
                "title": title,
                "subsection_number": None,
                "content": prefix,
            }

        for sub_idx, submatch in enumerate(subsections):
            sub_start = submatch.start()
            sub_end = (
                subsections[sub_idx + 1].start()
                if sub_idx + 1 < len(subsections)
                else len(content)
            )
            sub_number = submatch.group("num").strip()
            sub_content = content[sub_start:sub_end].strip()
            yield {
                "number": number,
                "title": title,
                "subsection_number": sub_number,
                "content": sub_content,
            }


def build_text_splitter(chunk_size, chunk_overlap, separators=None):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators or DEFAULT_SEPARATORS,
    )


def build_chunks(text, chunk_size, chunk_overlap, separators=None):
    splitter = build_text_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )
    return splitter.split_text(text)


def chunk_text(text, chunk_size=500, chunk_overlap=50, separators=None):
    chunks = []
    for section in iter_sections(text):
        chunks.extend(
            build_chunks(
                section["content"],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=separators,
            )
        )
    return chunks


def summarize_chunks(label, chunks, preview_count=3):
    lengths = [len(c) for c in chunks]
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    print(f"\n=== {label} ===")
    print(
        "chunks: "
        f"{len(chunks)}, avg_len: {avg_len:.1f}, "
        f"min: {min(lengths, default=0)}, max: {max(lengths, default=0)}"
    )
    for i, chunk in enumerate(chunks[:preview_count], start=1):
        print(f"\n[{label}] chunk {i} (len={len(chunk)}):")
        print(chunk[:1000].strip())
