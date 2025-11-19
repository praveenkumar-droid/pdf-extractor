"""
PROFESSIONAL RUNNER - Main entry point for PDF extraction
Provides a simple, unified interface for all extraction modes
"""
import sys
import argparse
from pathlib import Path
from typing import Optional, List

def check_dependencies() -> List[str]:
    """Check for missing dependencies"""
    missing = []
    
    required = [
        ('pdfplumber', 'pdfplumber'),
        ('tqdm', 'tqdm'),
        ('fastapi', 'fastapi'),
    ]
    
    optional = [
        ('fitz', 'pymupdf'),
        ('pdfminer', 'pdfminer.six'),
    ]
    
    for import_name, pip_name in required:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    
    return missing


def run_single(pdf_path: str, output_path: Optional[str] = None, 
               use_multi_engine: bool = False, enable_llm: bool = False,
               verbose: bool = True) -> str:
    """
    Run extraction on a single PDF file.
    
    Args:
        pdf_path: Path to PDF file
        output_path: Optional output path
        use_multi_engine: Use multi-engine consensus
        enable_llm: Enable LLM verification
        verbose: Print progress
        
    Returns:
        Path to output file
    """
    from master_extractor import MasterExtractor
    
    extractor = MasterExtractor(
        verbose=verbose,
        enable_llm_verification=enable_llm
    )
    
    result = extractor.extract(pdf_path)
    
    if output_path is None:
        output_path = str(Path(pdf_path).with_suffix('.txt'))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result.formatted_text)
    
    if verbose:
        print(f"\n✓ Output saved to: {output_path}")
        print(f"  Quality: {result.quality_grade} ({result.quality_report['overall_score']:.0f}/100)")
        print(f"  Words: {result.word_count:,}")
    
    return output_path


def run_batch(input_dir: str, output_dir: str = "output",
              parallel: bool = False, enable_llm: bool = False,
              verbose: bool = True):
    """
    Run extraction on all PDFs in a directory.
    
    Args:
        input_dir: Input directory with PDFs
        output_dir: Output directory for results
        parallel: Use parallel processing
        enable_llm: Enable LLM verification
        verbose: Print progress
    """
    from batch_processor import BatchProcessor
    
    processor = BatchProcessor(
        output_dir=output_dir,
        enable_llm=enable_llm,
        verbose=verbose
    )
    
    result = processor.process_folder(input_dir, parallel=parallel)
    
    # Generate reports
    processor.generate_csv_report(result, f"{output_dir}/report.csv")
    processor.generate_html_report(result, f"{output_dir}/report.html")
    
    return result


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the API server"""
    import uvicorn
    
    print("="*60)
    print("Starting PDF Extractor API Server")
    print("="*60)
    print(f"Web UI:   http://localhost:{port}/ui")
    print(f"API Docs: http://localhost:{port}/docs")
    print("="*60)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def main():
    parser = argparse.ArgumentParser(
        description='Professional PDF Text Extractor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract single PDF
  python professional_runner.py single "input/doc.pdf"
  
  # Extract with LLM verification
  python professional_runner.py single "input/doc.pdf" --llm
  
  # Batch process folder
  python professional_runner.py batch "input" "output"
  
  # Start API server
  python professional_runner.py api
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Single file command
    single_parser = subparsers.add_parser('single', help='Extract single PDF')
    single_parser.add_argument('pdf_path', help='Path to PDF file')
    single_parser.add_argument('-o', '--output', help='Output path')
    single_parser.add_argument('--multi-engine', action='store_true', help='Use multi-engine')
    single_parser.add_argument('--llm', action='store_true', help='Enable LLM verification')
    single_parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch process folder')
    batch_parser.add_argument('input_dir', help='Input directory')
    batch_parser.add_argument('output_dir', nargs='?', default='output', help='Output directory')
    batch_parser.add_argument('--parallel', action='store_true', help='Parallel processing')
    batch_parser.add_argument('--llm', action='store_true', help='Enable LLM verification')
    batch_parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    
    # API command
    api_parser = subparsers.add_parser('api', help='Start API server')
    api_parser.add_argument('--host', default='0.0.0.0', help='Host address')
    api_parser.add_argument('--port', type=int, default=8000, help='Port number')
    api_parser.add_argument('--reload', action='store_true', help='Auto-reload on changes')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check system status')
    
    args = parser.parse_args()
    
    if args.command == 'single':
        missing = check_dependencies()
        if missing:
            print(f"Missing dependencies: {', '.join(missing)}")
            print(f"Install with: pip install {' '.join(missing)}")
            sys.exit(1)
        
        run_single(
            args.pdf_path,
            args.output,
            args.multi_engine,
            args.llm,
            not args.quiet
        )
    
    elif args.command == 'batch':
        missing = check_dependencies()
        if missing:
            print(f"Missing dependencies: {', '.join(missing)}")
            sys.exit(1)
        
        run_batch(
            args.input_dir,
            args.output_dir,
            args.parallel,
            args.llm,
            not args.quiet
        )
    
    elif args.command == 'api':
        run_api(args.host, args.port, args.reload)
    
    elif args.command == 'check':
        print("Checking system...")
        missing = check_dependencies()
        if missing:
            print(f"❌ Missing: {', '.join(missing)}")
        else:
            print("✓ All dependencies installed")
        
        # Check modules
        try:
            from master_extractor import MasterExtractor
            print("✓ MasterExtractor OK")
        except Exception as e:
            print(f"❌ MasterExtractor: {e}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
