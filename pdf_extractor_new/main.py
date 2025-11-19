"""
Command Line Interface for PDF Extraction
Usage: python main.py [options]
"""
import argparse
import sys
from pathlib import Path

from processor import FileSystemProcessor
import config


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from Japanese PDFs in perfect reading order',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs in default input folder
  python main.py
  
  # Process specific folder
  python main.py -i "C:/my_pdfs" -o "C:/output"
  
  # Process single file
  python main.py -f "document.pdf"
  
  # Don't skip existing files
  python main.py --no-skip
        """
    )
    
    parser.add_argument(
        '-i', '--input',
        type=str,
        default=None,
        help=f'Input directory (default: {config.INPUT_DIR})'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help=f'Output directory (default: {config.OUTPUT_DIR})'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        default=None,
        help='Process single file instead of directory'
    )
    
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Reprocess files even if output exists'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Don\'t search subdirectories'
    )
    
    parser.add_argument(
        '--flat',
        action='store_true',
        help='Save all output files in flat structure (no subdirectories)'
    )
    
    args = parser.parse_args()
    
    # Override config with command line arguments
    if args.no_skip:
        config.SKIP_EXISTING = False
    
    if args.no_recursive:
        config.RECURSIVE_SCAN = False
    
    if args.flat:
        config.PRESERVE_DIRECTORY_STRUCTURE = False
    
    # Create processor
    processor = FileSystemProcessor(
        input_dir=args.input,
        output_dir=args.output
    )
    
    try:
        if args.file:
            # Single file mode
            print(f"\nProcessing single file: {args.file}")
            output_path = processor.process_file(args.file)
            print(f"✓ Extracted to: {output_path}")
            print(f"\nDone!")
        else:
            # Batch mode
            print(f"\nStarting batch processing...")
            print(f"Input:  {processor.input_dir}")
            print(f"Output: {processor.output_dir}\n")
            
            stats = processor.process_all()
            
            if stats['total'] == 0:
                print("\n⚠ No PDF files found in input directory!")
                print(f"Please place PDF files in: {processor.input_dir}")
            else:
                print(f"\n✓ Processing complete!")
                print(f"Successfully processed: {stats['success']}/{stats['total']} files")
                
                if stats['failed'] > 0:
                    print(f"⚠ {stats['failed']} files failed - check logs for details")
    
    except KeyboardInterrupt:
        print("\n\n⚠ Processing interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
