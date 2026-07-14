#!/usr/bin/env python3
"""
Analyze financial report PDFs: page count, embedded TOC, chapter markers.

Usage:
    python analyze_pdf.py <pdf_path> [<pdf_path2> ...]

Example:
    python analyze_pdf.py raw_pdfs/Tencent_2025_Annual_Report.pdf
"""

import fitz  # PyMuPDF
import sys
import os

# Add parent directory for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from preprocessing.config import CHAPTER_KEYWORDS


def analyze_pdf(pdf_path):
    """Analyze a single PDF: page count, TOC, chapter markers."""
    doc = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    total_pages = len(doc)

    print(f"\n{'='*60}")
    print(f"File: {filename}")
    print(f"Total pages: {total_pages}")
    print(f"{'='*60}\n")

    # Try to get embedded table of contents
    toc = doc.get_toc()
    if toc:
        print("Embedded TOC (Table of Contents):")
        print("-" * 60)
        for level, title, page in toc:
            indent = "  " * (level - 1)
            print(f"{indent}p.{page:>3}  {title}")
        print()
    else:
        print("No embedded TOC found. Scanning pages for chapter markers...\n")

    # Scan pages for chapter markers
    print("Chapter marker scan (first 5 words of each page):")
    print("-" * 60)
    scan_limit = min(len(doc), 350)
    for i in range(scan_limit):
        page = doc[i]
        text = page.get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        first_lines = ' '.join(lines[:5])
        for kw in CHAPTER_KEYWORDS:
            if kw in first_lines:
                print(f"  p.{i+1:>3}  [{kw}]  {first_lines[:80]}")
                break

    doc.close()

    # Print first 30 pages for structure understanding
    print(f"\n{'='*60}")
    print("Page-by-page first line (pages 1-30):")
    print("-" * 60)
    doc = fitz.open(pdf_path)
    for i in range(min(30, len(doc))):
        page = doc[i]
        text = page.get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        first_line = lines[0] if lines else "(empty/image only)"
        print(f"  p.{i+1:>3}  {first_line[:80]}")
    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_pdf.py <pdf_path> [<pdf_path2> ...]")
        print("Example: python analyze_pdf.py raw_pdfs/Tencent_2025_Annual_Report.pdf")
        sys.exit(1)

    for pdf in sys.argv[1:]:
        if not os.path.exists(pdf):
            print(f"File not found: {pdf}")
            continue
        analyze_pdf(pdf)
