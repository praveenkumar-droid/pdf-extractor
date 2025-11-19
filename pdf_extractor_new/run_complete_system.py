"""
COMPLETE PDF EXTRACTION SYSTEM - LOCAL RUNNER
Runs ALL implemented phases with full features

This script runs:
- Phase 0: Element Inventory
- Phase 1: Superscript/Subscript Detection
- Phase 2: Layout Analysis (Tables, Text Boxes)
- Phase 3: Smart Extraction Rules
- Phase 4: Character Preservation
- Phase 5: LLM Verification (Optional)
- Phase 6: Footnote Extraction
- Phase 7: Quality Scoring
- Phase 8: Error Handling
- Phase 9: Output Formatting
- Phase 10: Context Windows (for large docs)

Usage:
    python run_complete_system.py <pdf_path> [output_path]
    
Example:
    python run_complete_system.py "input/sample.pdf"
    python run_complete_system.py "input/sample.pdf" "output/result.txt"
    python run_complete_system.py "input/sample.pdf" --llm  # Enable LLM verification
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_dependencies():
    """Check if all required modules are available"""
    required_modules = [
        ('pdfplumber', 'pdfplumber'),
        ('config', 'config.py'),
        ('extractor', 'extractor.py'),
        ('element_inventory', 'element_inventory.py'),
        ('superscript_detector', 'superscript_detector.py'),
        ('layout_analyzer', 'layout_analyzer.py'),
        ('footnote_extractor', 'footnote_extractor.py'),
        ('llm_verifier', 'llm_verifier.py'),
        ('quality_scorer', 'quality_scorer.py'),
        ('error_handler', 'error_handler.py'),
        ('output_formatter', 'output_formatter.py'),
        ('context_windows', 'context_windows.py'),
        ('master_extractor', 'master_extractor.py'),
    ]
    
    missing = []
    for module_name, file_name in required_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            missing.append((module_name, file_name, str(e)))
    
    return missing


def main():
    print("="*70)
    print("PDF EXTRACTION SYSTEM - COMPLETE LOCAL RUNNER")
    print("="*70)
    print()
    
    # Check arguments
    if len(sys.argv) < 2:
        print("Usage: python run_complete_system.py <pdf_path> [output_path] [--llm]")
        print()
        print("Options:")
        print("  --llm     Enable LLM verification (requires API key)")
        print("  --verbose Show detailed progress")
        print("  --quiet   Minimal output")
        print()
        print("Examples:")
        print('  python run_complete_system.py "input/document.pdf"')
        print('  python run_complete_system.py "input/document.pdf" "output/result.txt"')
        print('  python run_complete_system.py "input/document.pdf" --llm')
        sys.exit(1)
    
    # Parse arguments
    pdf_path = sys.argv[1]
    output_path = None
    enable_llm = False
    verbose = True
    
    for arg in sys.argv[2:]:
        if arg == "--llm":
            enable_llm = True
        elif arg == "--quiet":
            verbose = False
        elif arg == "--verbose":
            verbose = True
        elif not arg.startswith("--"):
            output_path = arg
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        print(f"ERROR: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print()
        print("ERROR: Missing required modules:")
        for module, filename, error in missing:
            print(f"  - {module} ({filename}): {error}")
        print()
        print("Please ensure all module files are in the same directory.")
        sys.exit(1)
    
    print("All dependencies OK!")
    print()
    
    # Import the master extractor
    from master_extractor import MasterExtractor
    
    # Create extractor with all features
    print("Initializing extraction system...")
    extractor = MasterExtractor(
        verbose=verbose,
        enable_llm_verification=enable_llm,
        llm_backend="mock",  # Change to "openai" or "anthropic" if you have API key
        max_chunk_size=100000,
        enable_chunking=True
    )
    
    print()
    print(f"Processing: {pdf_path}")
    print()
    
    # Run extraction
    try:
        result = extractor.extract(pdf_path)
        
        # Print detailed report
        extractor.print_report(result)
        
        # Save output
        if output_path is None:
            output_path = str(Path(pdf_path).with_suffix('.txt'))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.formatted_text)
        
        print(f"Output saved to: {output_path}")
        print()
        
        # Print quality summary
        print("="*70)
        print("QUALITY SUMMARY")
        print("="*70)
        print(f"Grade: {result.quality_grade}")
        print(f"Score: {result.quality_report['overall_score']:.1f}/100")
        print(f"Coverage: {result.inventory_report['coverage_percent']:.1f}%")
        print(f"Footnote Match: {result.footnote_report['match_rate']}%")
        print("="*70)
        
    except Exception as e:
        print(f"ERROR during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
