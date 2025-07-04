"""Centralised configuration for PRIMCS.

Environment variables:
  • PRIMCS_TMP_DIR    – custom temp directory
  • PRIMCS_TIMEOUT    – max seconds per run (default 10)
  • PRIMCS_MAX_OUTPUT – cap on stdout/stderr bytes (default 1 MB)
"""

import os
from pathlib import Path

TMP_DIR = Path(os.getenv("PRIMCS_TMP_DIR", "/tmp/primcs"))
TMP_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT_SECONDS = int(os.getenv("PRIMCS_TIMEOUT", "100"))
MAX_OUTPUT_BYTES = int(os.getenv("PRIMCS_MAX_OUTPUT", str(1024 * 1024)))  # 1MB
