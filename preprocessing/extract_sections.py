#!/usr/bin/env python3
"""
Extract core sections from financial report PDFs and clean noise.

Strips cover pages, director reports, corporate governance, auditor reports,
and disclaimer pages that add no retrieval value in a RAG system.

Outputs:
  - Clean PDFs (combined + per-section)
  - Markdown text files (combined + per-section)

Usage:
    python extract_sections.py [--raw-dir DIR] [--out-dir DIR]

Example:
    python extract_sections.py --raw-dir raw_pdfs --out-dir processed
"""

import fitz  # PyMuPDF
import os
import re
import argparse

# Add parent directory for config import
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys_path_inserted = False
if sys_path not in sys.sys_path:
    sys.sys_path.insert(0, sys_path)
    sys_path_inserted = True

import sys
from preprocessing.config import RAW_DIR, OUT_DIR, ANNUAL_SECTIONS, INTERIM_SECTIONS


def extract_pages_to_pdf(doc, start_page, end_page, output_path):
    """Extract a range of pages (0-indexed, inclusive) to a new PDF."""
    new_doc = fitz.open()
    for i in range(start_page, min(end_page + 1, len(doc))):
        new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(output_path)
    new_doc.close()


def extract_pages_to_markdown(doc, start_page, end_page):
    """Extract a range of pages to markdown text."""
    lines = []
    for i in range(start_page, min(end_page + 1, len(doc))):
        page = doc[i]
        text = page.get_text()
        # Clean up excessive blank lines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        lines.append(text.strip())
    return "\n\n---\n\n".join(lines)


def process_report(pdf_path, sections, report_label, out_dir):
    """Process a single report: extract sections to PDF + Markdown."""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    filename_base = os.path.splitext(os.path.basename(pdf_path))[0]

    print(f"\n{'='*60}")
    print(f"Processing: {filename_base} ({total_pages} pages)")
    print(f"{'='*60}")

    all_markdown = f"# {report_label}\n\n"
    extracted_page_count = 0

    for section_name, (start, end) in sections.items():
        actual_start = start
        actual_end = min(end, total_pages - 1)
        page_count = actual_end - actual_start + 1
        extracted_page_count += page_count

        # Output PDF
        pdf_out = os.path.join(out_dir, f"{filename_base}_{section_name}.pdf")
        extract_pages_to_pdf(doc, actual_start, actual_end, pdf_out)

        # Output Markdown
        md_text = extract_pages_to_markdown(doc, actual_start, actual_end)
        all_markdown += f"\n## {section_name}\n\n{md_text}\n"

        # Save individual section markdown
        md_out = os.path.join(out_dir, f"{filename_base}_{section_name}.md")
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write(f"# {report_label} - {section_name}\n\n{md_text}")

        print(f"  {section_name}: pages {actual_start+1}-{actual_end+1} ({page_count} pages) -> PDF + MD")

    # Save combined markdown
    combined_md_out = os.path.join(out_dir, f"{filename_base}_核心章节合集.md")
    with open(combined_md_out, 'w', encoding='utf-8') as f:
        f.write(all_markdown)

    # Create combined PDF
    combined_pdf_out = os.path.join(out_dir, f"{filename_base}_核心章节合集.pdf")
    new_doc = fitz.open()
    for section_name, (start, end) in sections.items():
        actual_end = min(end, total_pages - 1)
        for i in range(start, actual_end + 1):
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
    new_doc.save(combined_pdf_out)
    new_doc.close()

    skipped = total_pages - extracted_page_count
    print(f"\n  Total: {total_pages} pages -> extracted {extracted_page_count}, skipped {skipped} (noise)")
    print(f"  Combined PDF: {os.path.basename(combined_pdf_out)}")
    print(f"  Combined MD:  {os.path.basename(combined_md_out)}")

    doc.close()
    return {
        "total": total_pages,
        "extracted": extracted_page_count,
        "skipped": skipped,
        "sections": list(sections.keys()),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract core sections from financial report PDFs")
    parser.add_argument("--raw-dir", default=RAW_DIR, help="Directory containing raw PDF files")
    parser.add_argument("--out-dir", default=OUT_DIR, help="Output directory for processed files")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    results = {}

    # Process Annual Report
    annual_path = os.path.join(args.raw_dir, "Tencent_2025_Annual_Report.pdf")
    if os.path.exists(annual_path):
        results["annual"] = process_report(
            annual_path, ANNUAL_SECTIONS,
            "腾讯控股有限公司 2025 年度报告 - 核心章节",
            args.out_dir
        )
    else:
        print(f"File not found: {annual_path}")

    # Process Interim Report
    interim_path = os.path.join(args.raw_dir, "Tencent_2025_Interim_Report.pdf")
    if os.path.exists(interim_path):
        results["interim"] = process_report(
            interim_path, INTERIM_SECTIONS,
            "腾讯控股有限公司 2025 中期报告 - 核心章节",
            args.out_dir
        )
    else:
        print(f"File not found: {interim_path}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for key, r in results.items():
        print(f"\n  {key}:")
        print(f"    Total pages:    {r['total']}")
        print(f"    Extracted:      {r['extracted']} ({r['extracted']/r['total']*100:.0f}%)")
        print(f"    Skipped (noise): {r['skipped']} ({r['skipped']/r['total']*100:.0f}%)")
        print(f"    Sections:       {', '.join(r['sections'])}")
