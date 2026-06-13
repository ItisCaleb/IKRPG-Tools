from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PYVENDOR = ROOT / "work" / "pyvendor"
if PYVENDOR.exists():
    sys.path.insert(0, str(PYVENDOR))

from pypdf import PdfReader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("pages", help="PDF pages, e.g. 109-115 or 237,238")
    parser.add_argument("--chars", type=int, default=5000)
    args = parser.parse_args()

    wanted: list[int] = []
    for chunk in args.pages.split(","):
        if "-" in chunk:
            start, end = [int(part) for part in chunk.split("-", 1)]
            wanted.extend(range(start, end + 1))
        else:
            wanted.append(int(chunk))

    reader = PdfReader(str(args.pdf), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")

    for page_no in wanted:
        text = reader.pages[page_no - 1].extract_text() or ""
        cleaned = re.sub(r"[ \t]+", " ", text).strip()
        print(f"--- PDF page {page_no} ---")
        print(cleaned[: args.chars])


if __name__ == "__main__":
    main()
