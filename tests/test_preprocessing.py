#!/usr/bin/env python3
"""
Preprocessing unit tests.

Tests the core extraction logic without requiring actual PDF files.
Run with: python -m pytest tests/test_preprocessing.py -v
"""

import os
import sys
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from preprocessing.config import (
    ANNUAL_SECTIONS, INTERIM_SECTIONS,
    ANNUAL_SPLIT_SECTIONS, INTERIM_SPLIT_SECTIONS,
    CHAPTER_KEYWORDS, MAX_FILE_SIZE_BYTES,
)


def test_annual_sections_defined():
    """Verify annual report sections are properly defined."""
    assert len(ANNUAL_SECTIONS) == 7
    assert "03_管理层讨论与分析" in ANNUAL_SECTIONS
    # MD&A should cover at least 15 pages
    start, end = ANNUAL_SECTIONS["03_管理层讨论与分析"]
    assert end - start >= 15


def test_interim_sections_defined():
    """Verify interim report sections are properly defined."""
    assert len(INTERIM_SECTIONS) == 7
    assert "03_管理层讨论与分析" in INTERIM_SECTIONS
    start, end = INTERIM_SECTIONS["03_管理层讨论与分析"]
    assert end - start >= 10


def test_section_page_ranges_valid():
    """Verify all section page ranges have start < end."""
    for name, (start, end) in ANNUAL_SECTIONS.items():
        assert start <= end, f"Annual section {name}: start={start} > end={end}"
    for name, (start, end) in INTERIM_SECTIONS.items():
        assert start <= end, f"Interim section {name}: start={start} > end={end}"


def test_split_sections_format():
    """Verify split sections use tuple format (name, start, end)."""
    for sec in ANNUAL_SPLIT_SECTIONS:
        assert len(sec) == 3
        assert isinstance(sec[0], str)
        assert isinstance(sec[1], int)
        assert isinstance(sec[2], int)
        assert sec[1] <= sec[2]


def test_chapter_keywords_coverage():
    """Verify chapter keywords cover both simplified and traditional Chinese."""
    # Each keyword pair should cover both simplified and traditional
    assert "管理层讨论" in CHAPTER_KEYWORDS
    assert "管理层討論" in CHAPTER_KEYWORDS
    assert len(CHAPTER_KEYWORDS) >= 10


def test_max_file_size_bytes():
    """Verify max file size is under 10MB."""
    assert MAX_FILE_SIZE_BYTES < 10 * 1024 * 1024
    assert MAX_FILE_SIZE_BYTES > 0


def test_config_env_override():
    """Verify config can be overridden by environment variables."""
    original_raw = os.environ.get("RAW_PDF_DIR")
    os.environ["RAW_PDF_DIR"] = "/tmp/test_raw"
    # Re-import to pick up new env var
    import importlib
    import preprocessing.config as cfg
    importlib.reload(cfg)
    assert cfg.RAW_DIR == "/tmp/test_raw"
    # Restore
    if original_raw:
        os.environ["RAW_PDF_DIR"] = original_raw
    else:
        del os.environ["RAW_PDF_DIR"]
    importlib.reload(cfg)


if __name__ == "__main__":
    # Simple test runner without pytest
    test_functions = [
        test_annual_sections_defined,
        test_interim_sections_defined,
        test_section_page_ranges_valid,
        test_split_sections_format,
        test_chapter_keywords_coverage,
        test_max_file_size_bytes,
    ]

    passed = 0
    failed = 0
    for func in test_functions:
        try:
            func()
            print(f"  PASS  {func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {func.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {passed+failed} total")
