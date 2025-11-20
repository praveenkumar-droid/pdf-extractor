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
# Phase 0: Pre-analysis
ENABLE_ELEMENT_INVENTORY = True      # Element counting and inventory
ENABLE_PAGE_ANALYSIS = True          # Page-level pre-analysis

# Phase 1: Script detection
ENABLE_SUPERSCRIPT_DETECTION = True  # Superscript/subscript detection
ENABLE_SCRIPT_INTEGRATION = True     # Integrate scripts with base text

# Phase 2: Layout analysis
ENABLE_LAYOUT_ANALYSIS = True        # Tables, textboxes, regions
ENABLE_TABLE_DETECTION = True        # Table detection and extraction
ENABLE_TEXTBOX_EXTRACTION = True     # Text box extraction

# Phase 3-4: Text extraction
ENABLE_SMART_FILTERING = True        # Smart header/footer filtering
ENABLE_HORIZONTAL_BANDING = True     # Horizontal band grouping

# Phase 5: Verification
ENABLE_LLM_VERIFICATION = False      # LLM verification (disabled by default, requires API key)
ENABLE_ANTI_HALLUCINATION = True     # Anti-hallucination verification

# Phase 6: Footnotes
ENABLE_FOOTNOTE_EXTRACTION = True    # Footnote extraction
ENABLE_FOOTNOTE_MATCHING = True      # Match markers to definitions
ENABLE_CROSS_PAGE_FOOTNOTES = True   # Cross-page footnote matching

# Phase 7: Quality
ENABLE_QUALITY_SCORING = True        # Quality scoring system
ENABLE_ITERATIVE_VERIFICATION = True # Multiple verification passes

# Phase 8: Error handling
ENABLE_ERROR_RECOVERY = True         # Advanced error recovery
ENABLE_ROTATION_FIX = True           # Rotated page detection/fix
ENABLE_ENCODING_FALLBACK = True      # Encoding issue handling
ENABLE_OCR_DETECTION = True          # Scanned page detection
ENABLE_REMEDIATION_LOOP = True       # Quality remediation loop

# Phase 9: Output formatting
ENABLE_PAGE_MARKERS = True           # Add page markers to output
ENABLE_CONFIDENCE_MARKERS = True     # Add confidence annotations

# Phase 10: Large documents
ENABLE_CHUNKING = True               # Large document chunking
ENABLE_CONTEXT_WINDOWS = True        # Context window management

# Additional features
ENABLE_FLAGGING_SYSTEM = True        # Content flagging system
ENABLE_MULTI_ENGINE = False          # Multi-engine consensus (advanced)
ENABLE_BATCH_PROCESSING = True       # Batch processing support

# ═══════════════════════════════════════════════════════════════════
# TABLE DETECTION SETTINGS
# ═══════════════════════════════════════════════════════════════════
TABLE_DETECTION_MODE = "strict"      # Options: "strict" (borders only), "moderate", "aggressive" (text-based)
TABLE_MIN_ROWS = 3                   # Minimum rows for valid table (increased to reduce false positives)
TABLE_MIN_COLS = 3                   # Minimum columns for valid table
TABLE_MIN_CELLS = 9                  # Minimum total cells (rows × cols)
TABLE_ENABLE_TEXT_DETECTION = False  # DISABLED - text-based detection causes false positives

# ═══════════════════════════════════════════════════════════════════
# TABLE OUTPUT SETTINGS
# ═══════════════════════════════════════════════════════════════════
TABLE_OUTPUT_FORMAT = "markdown"     # Options: "markdown", "csv", "text", "json"
TABLE_INCLUDE_BORDERS = True         # Add borders in text format
TABLE_PRESERVE_ALIGNMENT = True      # Preserve column alignment
TABLE_MIN_CONFIDENCE = 0.7           # Minimum confidence to include table

# ═══════════════════════════════════════════════════════════════════
# FOOTNOTE OUTPUT SETTINGS
# ═══════════════════════════════════════════════════════════════════
FOOTNOTE_OUTPUT_FORMAT = "inline"    # Options: "inline", "endnotes", "separate"
FOOTNOTE_MARKER_FORMAT = "original"  # Options: "original", "numbered", "symbols"

# ═══════════════════════════════════════════════════════════════════
# QUALITY THRESHOLDS
# ═══════════════════════════════════════════════════════════════════
MIN_QUALITY_THRESHOLD = 70.0         # Minimum quality score (0-100)
REMEDIATION_THRESHOLD = 70.0         # Trigger remediation if below this
MAX_REMEDIATION_ATTEMPTS = 2         # Maximum remediation attempts

# ═══════════════════════════════════════════════════════════════════
# OUTPUT FORMATTING SETTINGS
# ═══════════════════════════════════════════════════════════════════
INCLUDE_PAGE_MARKERS = True          # Add page markers (--- Page N ---) to output
INCLUDE_STATISTICS = True            # Add statistics to output
INCLUDE_TIMESTAMP = True             # Add timestamp to output
INCLUDE_METADATA = True              # Include extraction metadata
INCLUDE_CONFIDENCE_SCORES = True     # Include confidence scores for flagged content

# ═══════════════════════════════════════════════════════════════════
# TEXT FORMATTING SETTINGS
# ═══════════════════════════════════════════════════════════════════
PRESERVE_WHITESPACE = True           # Preserve original whitespace
PRESERVE_LINE_BREAKS = True          # Preserve original line breaks
NORMALIZE_LINE_ENDINGS = False       # Convert all line endings to \n (disabled for fidelity)

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Performance
MAX_WORKERS = 4  # For parallel processing (future enhancement)
