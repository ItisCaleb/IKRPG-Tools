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
    parser.add_argument("terms", nargs="*", default=["contents", "race", "combat", "spell", "equipment", "gear"])
    parser.add_argument("--context", type=int, default=800)
    args = parser.parse_args()

    reader = PdfReader(str(args.pdf), strict=False)
    if reader.is_encrypted:
        reader.decrypt("")

    terms = [term.lower() for term in args.terms]
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        haystack = text.lower()
        if any(term in haystack for term in terms):
            cleaned = re.sub(r"\s+", " ", text).strip()
            print(f"--- PDF page {index + 1} ---")
            print(cleaned[: args.context])


if __name__ == "__main__":
    main()
