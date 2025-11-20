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

# ═══════════════════════════════════════════════════════════════════
# FEATURE ENABLE FLAGS (for extractor_integrated.py compatibility)
# ═══════════════════════════════════════════════════════════════════
ENABLE_ELEMENT_INVENTORY = True      # Phase 0: Element counting
ENABLE_SUPERSCRIPT_DETECTION = True  # Phase 1: Super/subscripts
ENABLE_LAYOUT_ANALYSIS = True        # Phase 2: Tables, textboxes
ENABLE_FOOTNOTE_EXTRACTION = True    # Phase 6: Footnotes
ENABLE_ANTI_HALLUCINATION = True     # Phase 5b: Anti-hallucination
ENABLE_ERROR_RECOVERY = True         # Phase 8: Error handling
ENABLE_QUALITY_SCORING = True        # Phase 7: Quality scoring
ENABLE_LLM_VERIFICATION = False      # Phase 5: LLM verification (disabled by default)
ENABLE_CHUNKING = True               # Phase 10: Large documents
ENABLE_ROTATION_FIX = True           # Error handler: Rotated pages
ENABLE_ENCODING_FALLBACK = True      # Error handler: Encoding issues
ENABLE_OCR_DETECTION = True          # Error handler: Scanned pages

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Performance
MAX_WORKERS = 4  # For parallel processing (future enhancement)
