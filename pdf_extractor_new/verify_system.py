"""
SYSTEM VERIFICATION - Check all connections and run test
Run this to verify your system is properly set up
"""

import sys
from pathlib import Path

print("="*70)
print("PDF EXTRACTION SYSTEM - COMPLETE VERIFICATION")
print("="*70)
print()

# Track results
all_ok = True
issues = []

# 1. Check all module imports
print("1. CHECKING MODULE IMPORTS")
print("-"*70)

modules = [
    ('pdfplumber', 'Core PDF library'),
    ('config', 'Configuration'),
    ('extractor', 'Phase 3+4: Text extraction'),
    ('element_inventory', 'Phase 0: Element counting'),
    ('superscript_detector', 'Phase 1: Super/subscript'),
    ('layout_analyzer', 'Phase 2: Tables/boxes'),
    ('footnote_extractor', 'Phase 6: Footnotes'),
    ('llm_verifier', 'Phase 5: LLM verification'),
    ('quality_scorer', 'Phase 7: Quality scoring'),
    ('error_handler', 'Phase 8: Error handling'),
    ('output_formatter', 'Phase 9: Output formatting'),
    ('context_windows', 'Phase 10: Large documents'),
    ('master_extractor', 'All phases integrated'),
    ('multi_engine_extractor', 'Multi-engine consensus'),
    ('batch_processor', 'Batch processing'),
    ('flagging_system', 'Review flags'),
]

for module_name, description in modules:
    try:
        __import__(module_name)
        print(f"  ✓ {module_name:25} {description}")
    except ImportError as e:
        print(f"  ✗ {module_name:25} MISSING: {e}")
        all_ok = False
        issues.append(f"Missing module: {module_name}")

print()

# 2. Check optional dependencies
print("2. CHECKING OPTIONAL DEPENDENCIES")
print("-"*70)

optional = [
    ('fitz', 'pymupdf', 'PyMuPDF engine'),
    ('pdfminer.high_level', 'pdfminer.six', 'PDFMiner engine'),
]

for import_name, pip_name, description in optional:
    try:
        __import__(import_name)
        print(f"  ✓ {pip_name:25} {description}")
    except ImportError:
        print(f"  ○ {pip_name:25} Not installed (optional)")

print()

# 3. Check class connections
print("3. CHECKING CLASS CONNECTIONS")
print("-"*70)

try:
    from master_extractor import MasterExtractor, ExtractionResult
    print("  ✓ MasterExtractor imports correctly")
    
    # Check that MasterExtractor has all expected attributes
    extractor = MasterExtractor(verbose=False)
    expected_attrs = [
        'text_extractor', 'inventory_analyzer', 'script_detector',
        'layout_analyzer', 'footnote_extractor', 'llm_verifier',
        'quality_scorer', 'output_formatter', 'error_handler',
        'large_doc_processor'
    ]
    
    for attr in expected_attrs:
        if hasattr(extractor, attr):
            print(f"    ✓ {attr}")
        else:
            print(f"    ✗ {attr} - MISSING")
            all_ok = False
            issues.append(f"MasterExtractor missing: {attr}")
            
except Exception as e:
    print(f"  ✗ MasterExtractor error: {e}")
    all_ok = False
    issues.append(f"MasterExtractor error: {e}")

print()

# 4. Check batch processor connection
print("4. CHECKING BATCH PROCESSOR")
print("-"*70)

try:
    from batch_processor import BatchProcessor, BatchResult
    print("  ✓ BatchProcessor imports correctly")
    
    # Check it can import master_extractor
    processor = BatchProcessor(verbose=False)
    print("  ✓ BatchProcessor initializes correctly")
    
except Exception as e:
    print(f"  ✗ BatchProcessor error: {e}")
    all_ok = False
    issues.append(f"BatchProcessor error: {e}")

print()

# 5. Check multi-engine extractor
print("5. CHECKING MULTI-ENGINE EXTRACTOR")
print("-"*70)

try:
    from multi_engine_extractor import MultiEngineExtractor, ConsensusResult
    print("  ✓ MultiEngineExtractor imports correctly")
    
    extractor = MultiEngineExtractor(verbose=False)
    print(f"  ✓ Engines configured: {len(extractor.engines)}")
    for engine in extractor.engines:
        print(f"    - {engine.name}")
        
except Exception as e:
    print(f"  ✗ MultiEngineExtractor error: {e}")
    all_ok = False
    issues.append(f"MultiEngineExtractor error: {e}")

print()

# 6. Check professional runner
print("6. CHECKING PROFESSIONAL RUNNER")
print("-"*70)

try:
    from professional_runner import check_dependencies, run_single, run_batch
    print("  ✓ professional_runner imports correctly")
    
    missing = check_dependencies()
    if missing:
        print(f"  ⚠ Missing dependencies: {missing}")
    else:
        print("  ✓ All dependencies available")
        
except Exception as e:
    print(f"  ✗ professional_runner error: {e}")
    all_ok = False
    issues.append(f"professional_runner error: {e}")

print()

# 7. Check directories
print("7. CHECKING DIRECTORIES")
print("-"*70)

dirs = ['input', 'output', 'logs', 'temp']
for d in dirs:
    path = Path(d)
    if path.exists():
        print(f"  ✓ {d}/")
    else:
        print(f"  ○ {d}/ (will be created when needed)")

print()

# Summary
print("="*70)
print("VERIFICATION SUMMARY")
print("="*70)
print()

if all_ok:
    print("✅ ALL SYSTEMS CONNECTED AND READY")
    print()
    print("You can now run:")
    print()
    print("  Single PDF extraction:")
    print('    python professional_runner.py single "input/file.pdf"')
    print()
    print("  With multi-engine:")
    print('    python professional_runner.py single "input/file.pdf" --multi-engine')
    print()
    print("  Batch processing:")
    print('    python professional_runner.py batch "input" "output"')
    print()
else:
    print("⚠️ ISSUES FOUND")
    print()
    for issue in issues:
        print(f"  • {issue}")
    print()
    print("Please fix the issues above before running extractions.")

print()
print("="*70)
