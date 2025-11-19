"""
SYSTEM CHECK - Verify all modules are working
Run this first to ensure everything is set up correctly
"""

import sys
from pathlib import Path

print("="*60)
print("PDF EXTRACTION SYSTEM - MODULE CHECK")
print("="*60)
print()

# Check Python version
print(f"Python Version: {sys.version}")
print()

# Check each module
modules_to_check = [
    ("pdfplumber", "PDF processing library"),
    ("config", "Configuration settings"),
    ("extractor", "Core PDF extractor"),
    ("element_inventory", "Phase 0: Element inventory"),
    ("superscript_detector", "Phase 1: Superscript/subscript detection"),
    ("layout_analyzer", "Phase 2: Layout analysis"),
    ("footnote_extractor", "Phase 6: Footnote extraction"),
    ("llm_verifier", "Phase 5: LLM verification"),
    ("quality_scorer", "Phase 7: Quality scoring"),
    ("error_handler", "Phase 8: Error handling"),
    ("output_formatter", "Phase 9: Output formatting"),
    ("context_windows", "Phase 10: Context windows"),
    ("master_extractor", "Master extractor (all phases)"),
]

print("Checking modules:")
print("-"*60)

all_ok = True
for module_name, description in modules_to_check:
    try:
        module = __import__(module_name)
        status = "✓ OK"
    except ImportError as e:
        status = f"✗ MISSING - {e}"
        all_ok = False
    except Exception as e:
        status = f"⚠ ERROR - {e}"
        all_ok = False
    
    print(f"  {module_name:25} {status}")

print("-"*60)
print()

if all_ok:
    print("✓ All modules loaded successfully!")
    print()
    print("You can now run:")
    print('  python run_complete_system.py "your_file.pdf"')
    print()
    print("Or on Windows:")
    print('  run_system.bat "your_file.pdf"')
else:
    print("✗ Some modules are missing or have errors.")
    print()
    print("Please ensure:")
    print("1. All .py files are in the same directory")
    print("2. pdfplumber is installed: pip install pdfplumber")

print()
print("="*60)
