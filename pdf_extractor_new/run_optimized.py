"""
SIMPLE RUNNER FOR OPTIMIZED PDF EXTRACTION
==========================================

Easy-to-use script for 95%+ accuracy extraction.
Just run: python run_optimized.py your_file.pdf
"""
import sys
import os
from pathlib import Path


def main():
    print("\n" + "="*60)
    print("PDF EXTRACTOR - 95%+ ACCURACY MODE")
    print("="*60)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("\nUsage: python run_optimized.py <pdf_file> [output_file]")
        print("\nExamples:")
        print("  python run_optimized.py document.pdf")
        print("  python run_optimized.py input/report.pdf output/result.txt")
        print("\nThe script will:")
        print("  1. Check your configuration")
        print("  2. Extract text with maximum accuracy")
        print("  3. Apply LLM verification")
        print("  4. Detect and format tables")
        print("  5. Extract footnotes")
        print("  6. Generate quality report")
        print("  7. Save output with all metadata")
        return 1
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if PDF exists
    if not Path(pdf_path).exists():
        print(f"\n❌ Error: File not found: {pdf_path}")
        return 1
    
    # Check configuration
    print("\n[1/3] Checking configuration...")
    try:
        import config_optimized as config
        
        # Check API key
        if config.LLM_API_KEY == "your-api-key-here":
            print("\n⚠ WARNING: LLM API key not configured!")
            print("  Edit config_optimized.py and set LLM_API_KEY")
            print("  Or set environment variable ANTHROPIC_API_KEY")
            print("\n  Continuing without LLM verification (reduced accuracy)...")
            config.LLM_ENABLED = False
        else:
            print(f"  ✓ LLM configured: {config.LLM_BACKEND}")
        
        print(f"  ✓ Target quality: {config.MIN_ACCEPTABLE_QUALITY}+")
        print(f"  ✓ Multi-engine: {config.MULTI_ENGINE_ENABLED}")
        
    except ImportError as e:
        print(f"\n❌ Error: Could not load configuration: {e}")
        print("  Make sure config_optimized.py exists in the same directory")
        return 1
    
    # Run extraction
    print("\n[2/3] Running optimized extraction...")
    try:
        from optimized_extractor import OptimizedPDFExtractor
        
        extractor = OptimizedPDFExtractor(verbose=True)
        result = extractor.extract(pdf_path)
        
    except Exception as e:
        print(f"\n❌ Extraction error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Save output
    print("\n[3/3] Saving output...")
    
    if output_path is None:
        output_path = str(Path(pdf_path).with_suffix('.optimized.txt'))
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.formatted_text)
        
        print(f"  ✓ Saved to: {output_path}")
        
        # Also save summary
        summary_path = str(Path(output_path).with_suffix('.summary.txt'))
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("EXTRACTION SUMMARY\n")
            f.write("="*40 + "\n\n")
            for key, value in result.to_summary().items():
                f.write(f"{key}: {value}\n")
        
        print(f"  ✓ Summary: {summary_path}")
        
    except Exception as e:
        print(f"\n❌ Error saving output: {e}")
        return 1
    
    # Final report
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    
    summary = result.to_summary()
    
    print(f"\nFile: {summary['filename']}")
    print(f"Pages: {summary['pages']}")
    print(f"Words: {summary['words']:,}")
    print(f"Quality: {summary['quality_score']}/100 ({summary['quality_grade']})")
    print(f"Confidence: {summary['confidence']:.0%}")
    print(f"Tables: {summary['tables']}")
    print(f"Footnotes: {summary['footnotes']}")
    print(f"Corrections: {summary['corrections']}")
    print(f"Time: {summary['time']}s")
    
    # Quality assessment
    if summary['quality_score'] >= 95:
        print("\n✅ SUCCESS: Achieved 95%+ accuracy target!")
    elif summary['quality_score'] >= 90:
        print("\n🟡 GOOD: Near target (90-95%)")
        print("   Consider enabling LLM verification for higher accuracy")
    elif summary['quality_score'] >= 80:
        print("\n🟠 ACCEPTABLE: 80-90% accuracy")
        print("   Review flagged sections for manual correction")
    else:
        print("\n🔴 NEEDS REVIEW: Below 80%")
        print("   Document may have complex layout or be scanned")
    
    # Show flags if any
    if result.flags:
        unresolved = [f for f in result.flags if not f.get('resolved', False)]
        if unresolved:
            print(f"\n⚠ {len(unresolved)} items flagged for review:")
            for flag in unresolved[:3]:
                print(f"   • Page {flag['page']}: {flag['message']}")
            if len(unresolved) > 3:
                print(f"   ... and {len(unresolved) - 3} more")
    
    print("\n" + "="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
