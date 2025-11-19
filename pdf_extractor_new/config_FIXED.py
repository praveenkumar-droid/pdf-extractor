"""
Configuration settings for PDF Extractor
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Directory paths
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Extraction settings
COLUMN_GAP_THRESHOLD = 50  # pixels - gap size to detect new column
LINE_HEIGHT_THRESHOLD = 15  # pixels - max Y-distance for same line
MARGIN_TOP_PERCENT = 0.05  # Top 5% is margin (headers)
MARGIN_BOTTOM_PERCENT = 0.95  # Bottom 5% is margin (footers)

# Processing settings
SKIP_EXISTING = True  # Skip files that already have output
RECURSIVE_SCAN = True  # Search subdirectories
PRESERVE_DIRECTORY_STRUCTURE = True  # Maintain folder structure in output

# ═══════════════════════════════════════════════════════════════════
# CHARACTER PRESERVATION - CRITICAL SETTING
# ═══════════════════════════════════════════════════════════════════
# Per LLM extraction specs: "EXTRACT ONLY - NEVER TRANSFORM"
# All characters MUST be preserved exactly as they appear in PDF
# DO NOT ENABLE these settings - they violate extraction fidelity rules
# ═══════════════════════════════════════════════════════════════════
NORMALIZE_CHARACTERS = False  # DISABLED - Violates "no transformation" rule
NORMALIZE_KATAKANA = False    # DISABLED - Violates "no transformation" rule
# ═══════════════════════════════════════════════════════════════════

# Cleanup settings (minimal, non-transformative)
REMOVE_HEADERS_FOOTERS = True
REMOVE_PAGE_NUMBERS = True
FIX_SPACING = True       # Optional - can be disabled if needed
JOIN_LINES = True        # Optional - can be disabled if needed
FIX_PUNCTUATION = True   # Optional - can be disabled if needed

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Performance
MAX_WORKERS = 4  # For parallel processing (future enhancement)
