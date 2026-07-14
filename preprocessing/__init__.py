"""Preprocessing module for financial report PDFs.

Provides tools for:
- Analyzing PDF structure (TOC, chapter markers)
- Extracting core financial sections
- Splitting large PDFs into upload-friendly chunks (<10MB)
"""

from .config import RAW_DIR, OUT_DIR, MAX_FILE_SIZE_MB
