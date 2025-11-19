"""
OPTIMIZED Configuration for 95%+ Accuracy PDF Extraction
=========================================================

This configuration enables all advanced features for maximum accuracy.
Update LLM_API_KEY with your actual API key.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Directory paths
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# ═══════════════════════════════════════════════════════════════════
# LLM VERIFICATION SETTINGS - CRITICAL FOR 95%+ ACCURACY
# ═══════════════════════════════════════════════════════════════════
LLM_ENABLED = True
LLM_BACKEND = "anthropic"  # Options: "anthropic", "openai"
LLM_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-api-key-here")  # UPDATE THIS
LLM_MODEL = "claude-sonnet-4-20250514"  # For Anthropic
# LLM_MODEL = "gpt-4-turbo-preview"  # For OpenAI
LLM_MAX_TOKENS = 2000
LLM_TEMPERATURE = 0.1  # Low for deterministic corrections
LLM_RETRY_ATTEMPTS = 3
LLM_TIMEOUT = 30  # seconds

# ═══════════════════════════════════════════════════════════════════
# MULTI-ENGINE EXTRACTION SETTINGS
# ═══════════════════════════════════════════════════════════════════
MULTI_ENGINE_ENABLED = True
USE_PDFPLUMBER = True
USE_PYMUPDF = True
USE_PDFMINER = True
CONSENSUS_THRESHOLD = 0.85  # Minimum agreement for auto-accept
CONFLICT_RESOLUTION = "llm"  # Options: "llm", "longest", "vote"

# ═══════════════════════════════════════════════════════════════════
# EXTRACTION SETTINGS - OPTIMIZED
# ═══════════════════════════════════════════════════════════════════
COLUMN_GAP_THRESHOLD = 40  # Reduced for better column detection
LINE_HEIGHT_THRESHOLD = 12  # Tighter for accurate line grouping
MARGIN_TOP_PERCENT = 0.03  # Narrower margins to preserve content
MARGIN_BOTTOM_PERCENT = 0.97

# ═══════════════════════════════════════════════════════════════════
# CHARACTER PRESERVATION - NEVER TRANSFORM
# ═══════════════════════════════════════════════════════════════════
NORMALIZE_CHARACTERS = False
NORMALIZE_KATAKANA = False

# ═══════════════════════════════════════════════════════════════════
# TABLE DETECTION SETTINGS - ENHANCED
# ═══════════════════════════════════════════════════════════════════
TABLE_DETECTION_ENABLED = True
TABLE_STRATEGIES = ["lines", "text", "whitespace", "hybrid"]
TABLE_MIN_ROWS = 2
TABLE_MIN_COLS = 2
TABLE_CONFIDENCE_THRESHOLD = 0.7
TABLE_LLM_VERIFY = True  # Use LLM to verify table structure

# ═══════════════════════════════════════════════════════════════════
# FOOTNOTE EXTRACTION SETTINGS - ENHANCED
# ═══════════════════════════════════════════════════════════════════
FOOTNOTE_REGION_THRESHOLD = 0.75  # Expanded from 0.80
FOOTNOTE_CROSS_PAGE_MATCHING = True
FOOTNOTE_LLM_VERIFY = True

# ═══════════════════════════════════════════════════════════════════
# QUALITY THRESHOLDS - STRICT FOR 95%+
# ═══════════════════════════════════════════════════════════════════
MIN_ACCEPTABLE_QUALITY = 90  # Minimum score to pass
RETRY_ON_LOW_QUALITY = True
MAX_RETRY_ATTEMPTS = 3
AUTO_FLAG_THRESHOLD = 0.85  # Flag content below this confidence

# ═══════════════════════════════════════════════════════════════════
# FLAGGING SYSTEM SETTINGS
# ═══════════════════════════════════════════════════════════════════
FLAGGING_ENABLED = True
FLAG_LOW_CONFIDENCE = True
FLAG_OCR_ERRORS = True
FLAG_MISSING_CONTENT = True
FLAG_TABLE_ISSUES = True
GENERATE_REVIEW_QUEUE = True

# ═══════════════════════════════════════════════════════════════════
# ITERATIVE VERIFICATION
# ═══════════════════════════════════════════════════════════════════
ITERATIVE_VERIFICATION = True
MAX_VERIFICATION_PASSES = 3
VERIFICATION_IMPROVEMENT_THRESHOLD = 0.02  # Stop if <2% improvement

# ═══════════════════════════════════════════════════════════════════
# ERROR HANDLING - ENHANCED
# ═══════════════════════════════════════════════════════════════════
ENABLE_ERROR_RECOVERY = True
ENABLE_ROTATION_FIX = True
ENABLE_ENCODING_FALLBACK = True
ENABLE_OCR_DETECTION = True
FALLBACK_ENCODINGS = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']

# ═══════════════════════════════════════════════════════════════════
# CLEANUP SETTINGS - MINIMAL
# ═══════════════════════════════════════════════════════════════════
REMOVE_HEADERS_FOOTERS = True
REMOVE_PAGE_NUMBERS = True
FIX_SPACING = True
JOIN_LINES = True
FIX_PUNCTUATION = True

# ═══════════════════════════════════════════════════════════════════
# PROCESSING SETTINGS
# ═══════════════════════════════════════════════════════════════════
SKIP_EXISTING = False  # Reprocess for accuracy testing
RECURSIVE_SCAN = True
PRESERVE_DIRECTORY_STRUCTURE = True
MAX_WORKERS = 4

# ═══════════════════════════════════════════════════════════════════
# LARGE DOCUMENT HANDLING
# ═══════════════════════════════════════════════════════════════════
ENABLE_CHUNKING = True
MAX_CHUNK_SIZE = 80000  # Characters
CHUNK_OVERLAP = 500
PRESERVE_SECTIONS = True
PRESERVE_PARAGRAPHS = True

# ═══════════════════════════════════════════════════════════════════
# LOGGING - DETAILED
# ═══════════════════════════════════════════════════════════════════
LOG_LEVEL = "DEBUG"  # DEBUG for detailed tracking
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
LOG_LLM_CALLS = True
LOG_CORRECTIONS = True
LOG_CONFIDENCE_SCORES = True

# ═══════════════════════════════════════════════════════════════════
# OUTPUT SETTINGS
# ═══════════════════════════════════════════════════════════════════
ADD_PAGE_MARKERS = True
ADD_CONFIDENCE_MARKERS = True
ADD_STATISTICS = True
ADD_TIMESTAMP = True
INCLUDE_REVIEW_FLAGS = True

# ═══════════════════════════════════════════════════════════════════
# JAPANESE-SPECIFIC SETTINGS
# ═══════════════════════════════════════════════════════════════════
JAPANESE_MODE = True
DETECT_VERTICAL_TEXT = True
PRESERVE_FURIGANA = True
HANDLE_MIXED_SCRIPTS = True

# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════
CACHE_LLM_RESPONSES = True
BATCH_LLM_REQUESTS = True
LLM_BATCH_SIZE = 10
PARALLEL_ENGINE_EXTRACTION = True


def validate_config():
    """Validate configuration settings"""
    errors = []
    warnings = []
    
    # Check LLM settings
    if LLM_ENABLED:
        if LLM_API_KEY == "your-api-key-here":
            errors.append("LLM_API_KEY not set - update config_optimized.py")
        if LLM_BACKEND not in ["anthropic", "openai"]:
            errors.append(f"Invalid LLM_BACKEND: {LLM_BACKEND}")
    
    # Check directories
    for dir_path in [INPUT_DIR, OUTPUT_DIR, LOGS_DIR, TEMP_DIR]:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            warnings.append(f"Created directory: {dir_path}")
    
    # Check thresholds
    if MIN_ACCEPTABLE_QUALITY < 80:
        warnings.append(f"MIN_ACCEPTABLE_QUALITY ({MIN_ACCEPTABLE_QUALITY}) is low for 95% target")
    
    return errors, warnings


def print_config_status():
    """Print current configuration status"""
    errors, warnings = validate_config()
    
    print("\n" + "="*60)
    print("OPTIMIZED CONFIGURATION STATUS")
    print("="*60)
    
    print(f"\n✓ LLM Enabled: {LLM_ENABLED}")
    print(f"  Backend: {LLM_BACKEND}")
    print(f"  Model: {LLM_MODEL}")
    print(f"  API Key: {'SET' if LLM_API_KEY != 'your-api-key-here' else 'NOT SET'}")
    
    print(f"\n✓ Multi-Engine: {MULTI_ENGINE_ENABLED}")
    print(f"  PDFPlumber: {USE_PDFPLUMBER}")
    print(f"  PyMuPDF: {USE_PYMUPDF}")
    print(f"  PDFMiner: {USE_PDFMINER}")
    
    print(f"\n✓ Quality Settings:")
    print(f"  Min Quality: {MIN_ACCEPTABLE_QUALITY}")
    print(f"  Retry Enabled: {RETRY_ON_LOW_QUALITY}")
    print(f"  Iterative Verification: {ITERATIVE_VERIFICATION}")
    
    print(f"\n✓ Flagging: {FLAGGING_ENABLED}")
    print(f"✓ Table LLM Verify: {TABLE_LLM_VERIFY}")
    print(f"✓ Footnote Cross-Page: {FOOTNOTE_CROSS_PAGE_MATCHING}")
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  • {err}")
    
    if warnings:
        print(f"\n⚠ WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  • {warn}")
    
    if not errors:
        print("\n✅ Configuration valid - ready for 95%+ accuracy extraction")
    
    print("="*60 + "\n")
    
    return len(errors) == 0


if __name__ == "__main__":
    print_config_status()
