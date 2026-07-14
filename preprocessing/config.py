"""Centralized configuration for preprocessing scripts.

Path defaults can be overridden via environment variables or CLI args,
so the scripts are portable across different machines.
"""

import os

# Source PDF directory (override with RAW_PDF_DIR env var)
RAW_DIR = os.environ.get("RAW_PDF_DIR", "./raw_pdfs")

# Output directory (override with OUTPUT_DIR env var)
OUT_DIR = os.environ.get("OUTPUT_DIR", "./processed")

# Maximum file size for Dify upload (in MB)
MAX_FILE_SIZE_MB = 10

# Safety margin: split at 9.5MB to stay under 10MB limit
MAX_FILE_SIZE_BYTES = int((MAX_FILE_SIZE_MB - 0.5) * 1024 * 1024)

# ============================================================
# Section definitions for Tencent 2025 financial reports
# Pages are 0-indexed (PyMuPDF convention)
# ============================================================

ANNUAL_SECTIONS = {
    "01_财务概要": (3, 4),
    "02_主席报告": (4, 7),
    "03_管理层讨论与分析": (7, 26),
    "04_综合收益表": (129, 130),
    "05_综合财务状况表": (131, 134),
    "06_综合权益变动表": (134, 138),
    "07_综合现金流量表": (138, 140),
}

INTERIM_SECTIONS = {
    "01_财务表现摘要": (3, 5),
    "02_主席报告": (5, 8),
    "03_管理层讨论与分析": (8, 22),
    "04_简明综合收益表": (23, 25),
    "05_简明综合财务状况表": (25, 28),
    "06_简明综合权益变动表": (28, 32),
    "07_简明综合现金流量表": (32, 34),
}

# Section boundaries for smart splitting (0-indexed page ranges)
ANNUAL_SPLIT_SECTIONS = [
    ("01_财务概要", 3, 4),
    ("02_主席报告", 4, 7),
    ("03_管理层讨论与分析", 7, 26),
    ("04_综合收益表", 27, 28),
    ("05_综合财务状况表", 29, 32),
    ("06_综合权益变动表", 33, 37),
    ("07_综合现金流量表", 38, 40),
]

INTERIM_SPLIT_SECTIONS = [
    ("01_财务表现摘要", 3, 5),
    ("02_主席报告", 5, 8),
    ("03_管理层讨论与分析", 8, 22),
    ("04_简明综合收益表", 23, 25),
    ("05_简明综合财务状况表", 26, 29),
    ("06_简明综合权益变动表", 30, 34),
    ("07_简明综合现金流量表", 35, 37),
]

# Chapter keywords for PDF analysis
CHAPTER_KEYWORDS = [
    "管理层讨论", "管理层討論",
    "业务回顾", "業務回顧",
    "合并综合损益", "合併綜合損益",
    "综合损益", "綜合損益",
    "财务报表", "財務報表",
    "独立核数师", "獨立核數師",
    "董事会报告", "董事會報告",
    "企业管治", "企業管治",
    "主席报告", "主席報告",
    "风险管理", "風險管理",
    "目录", "目錄",
    "免责", "免責",
    "公司治理",
]
