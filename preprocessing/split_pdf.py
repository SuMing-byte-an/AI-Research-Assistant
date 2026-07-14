#!/usr/bin/env python3
"""
Split combined PDFs into parts under a size limit (default 10MB).
Splits at section boundaries where possible, and by individual pages
for oversized sections.

Usage:
    python split_pdf.py [--raw-dir DIR] [--out-dir DIR] [--max-size-mb N]

Example:
    python split_pdf.py --raw-dir processed --out-dir split --max-size-mb 10
"""

import fitz
import os
import tempfile
import argparse

sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if sys_path not in sys.sys_path:
    sys.sys_path.insert(0, sys_path)

from preprocessing.config import (
    OUT_DIR, MAX_FILE_SIZE_BYTES,
    ANNUAL_SPLIT_SECTIONS, INTERIM_SPLIT_SECTIONS,
)


def get_part_size(doc, start, end):
    """Get the file size of a page range by saving to temp."""
    tmp = fitz.open()
    for i in range(start, min(end + 1, len(doc))):
        tmp.insert_pdf(doc, from_page=i, to_page=i)
    tmp_path = os.path.join(tempfile.gettempdir(), "size_check.pdf")
    tmp.save(tmp_path)
    size = os.path.getsize(tmp_path)
    tmp.close()
    os.remove(tmp_path)
    return size


def split_pdf(pdf_path, sections, label, out_dir, max_size):
    """Split a PDF into parts under max_size, respecting section boundaries."""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    basename = os.path.splitext(os.path.basename(pdf_path))[0].replace("_核心章节合集", "")

    print(f"\n{'='*60}")
    print(f"Splitting: {basename} ({total_pages} pages)")
    print(f"{'='*60}")

    parts = []
    current_part_sections = []
    current_start = None
    current_end = None
    current_size = 0

    for sec_name, sec_start, sec_end in sections:
        sec_start = max(0, sec_start)
        sec_end = min(sec_end, total_pages - 1)
        sec_size = get_part_size(doc, sec_start, sec_end)

        if current_start is None:
            current_start = sec_start
            current_end = sec_end
            current_size = sec_size
            current_part_sections.append(sec_name)
        elif current_size + sec_size <= max_size:
            current_end = sec_end
            current_size += sec_size
            current_part_sections.append(sec_name)
        else:
            parts.append((current_start, current_end, current_part_sections[:], current_size))
            current_start = sec_start
            current_end = sec_end
            current_size = sec_size
            current_part_sections = [sec_name]

    # Don't forget the last part
    if current_start is not None:
        parts.append((current_start, current_end, current_part_sections[:], current_size))

    # Split oversized sections by individual pages
    final_parts = []
    for start, end, sec_names, est_size in parts:
        if est_size <= max_size:
            final_parts.append((start, end, sec_names))
        else:
            print(f"  Section {sec_names} too large ({est_size/1024/1024:.1f}MB), splitting by pages...")
            sub_start = start
            sub_size = 0
            for i in range(start, end + 1):
                page_size = get_part_size(doc, i, i)
                if sub_size + page_size > max_size and sub_start < i:
                    final_parts.append((sub_start, i - 1, sec_names[:]))
                    sub_start = i
                    sub_size = page_size
                else:
                    sub_size += page_size
            if sub_start <= end:
                final_parts.append((sub_start, end, sec_names[:]))

    # Save each part
    output_files = []
    for idx, (start, end, sec_names) in enumerate(final_parts, 1):
        part_doc = fitz.open()
        for i in range(start, end + 1):
            part_doc.insert_pdf(doc, from_page=i, to_page=i)

        out_name = f"{basename}_Part{idx}.pdf"
        out_path = os.path.join(out_dir, out_name)
        part_doc.save(out_path)
        actual_size = os.path.getsize(out_path)
        part_doc.close()

        page_count = end - start + 1
        sec_str = " + ".join(sec_names)
        print(f"  Part {idx}: pages {start+1}-{end+1} ({page_count} pages), {actual_size/1024/1024:.1f}MB")
        print(f"          sections: {sec_str}")
        output_files.append((out_path, actual_size))

    doc.close()
    return output_files


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split PDFs into size-limited parts")
    parser.add_argument("--raw-dir", default=OUT_DIR, help="Directory with combined PDFs")
    parser.add_argument("--out-dir", default="./split", help="Output directory for split files")
    parser.add_argument("--max-size-mb", type=float, default=10, help="Max file size in MB")
    args = parser.parse_args()

    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    max_size = int((args.max_size_mb - 0.5) * 1024 * 1024)

    all_outputs = []

    # Annual Report
    annual_path = os.path.join(args.raw_dir, "Tencent_2025_Annual_Report_核心章节合集.pdf")
    if os.path.exists(annual_path):
        all_outputs += split_pdf(annual_path, ANNUAL_SPLIT_SECTIONS, "Annual", out_dir, max_size)

    # Interim Report
    interim_path = os.path.join(args.raw_dir, "Tencent_2025_Interim_Report_核心章节合集.pdf")
    if os.path.exists(interim_path):
        all_outputs += split_pdf(interim_path, INTERIM_SPLIT_SECTIONS, "Interim", out_dir, max_size)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for path, size in all_outputs:
        limit_mb = args.max_size_mb
        status = "OK" if size < limit_mb * 1024 * 1024 else "OVER LIMIT!"
        print(f"  {status}  {os.path.basename(path):<50} {size/1024/1024:.1f}MB")
