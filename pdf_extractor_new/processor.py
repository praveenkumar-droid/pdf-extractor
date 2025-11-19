"""
Filesystem Batch Processor for PDF Extraction
Handles multiple files, folders, logging, and error recovery
"""
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List
import json

from extractor import JapanesePDFExtractor
import config


class FileSystemProcessor:
    """Processes multiple PDF files from filesystem"""
    
    def __init__(self, input_dir: str = None, output_dir: str = None):
        self.input_dir = Path(input_dir or config.INPUT_DIR)
        self.output_dir = Path(output_dir or config.OUTPUT_DIR)
        self.logs_dir = Path(config.LOGS_DIR)
        
        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize extractor
        self.extractor = JapanesePDFExtractor()
        
        # Statistics
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'failed_files': []
        }
    
    def _setup_logging(self):
        """Setup logging to file and console"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.logs_dir / f'processing_{timestamp}.log'
        
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format=config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("="*60)
        self.logger.info("PDF Extraction Started")
        self.logger.info(f"Input:  {self.input_dir}")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info("="*60)
    
    def find_pdfs(self) -> List[Path]:
        """Find all PDF files in input directory"""
        if config.RECURSIVE_SCAN:
            pdf_files = list(self.input_dir.rglob('*.pdf'))
        else:
            pdf_files = list(self.input_dir.glob('*.pdf'))
        
        self.logger.info(f"Found {len(pdf_files)} PDF files")
        return pdf_files
    
    def process_all(self) -> Dict:
        """
        Process all PDFs in input directory
        
        Returns:
            Statistics dictionary with results
        """
        pdf_files = self.find_pdfs()
        
        if not pdf_files:
            self.logger.warning("No PDF files found!")
            return self.stats
        
        self.stats['total'] = len(pdf_files)
        
        # Process each file with progress bar
        for pdf_path in tqdm(pdf_files, desc="Processing PDFs", unit="file"):
            self.process_single(pdf_path)
        
        # Generate summary report
        self._generate_report()
        
        return self.stats
    
    def process_single(self, pdf_path: Path):
        """Process a single PDF file"""
        try:
            # Determine output path
            if config.PRESERVE_DIRECTORY_STRUCTURE:
                # Maintain folder structure
                relative_path = pdf_path.relative_to(self.input_dir)
                output_path = self.output_dir / relative_path.with_suffix('.txt')
            else:
                # Flat structure
                output_path = self.output_dir / f"{pdf_path.stem}.txt"
            
            # Create output subdirectories if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Skip if already processed
            if config.SKIP_EXISTING and output_path.exists():
                self.logger.info(f"⊘ Skipped (exists): {pdf_path.name}")
                self.stats['skipped'] += 1
                return
            
            # Extract text
            self.logger.info(f"Processing: {pdf_path.name}")
            text = self.extractor.extract_pdf(str(pdf_path))
            
            # Save result
            output_path.write_text(text, encoding='utf-8')
            
            # Log character count
            char_count = len(text)
            self.logger.info(f"✓ Success: {pdf_path.name} ({char_count:,} chars)")
            self.stats['success'] += 1
            
        except Exception as e:
            error_msg = f"{pdf_path.name}: {str(e)}"
            self.logger.error(f"✗ Failed: {error_msg}")
            self.stats['failed'] += 1
            self.stats['failed_files'].append({
                'file': str(pdf_path),
                'error': str(e)
            })
    
    def _generate_report(self):
        """Generate processing summary report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.logs_dir / f'report_{timestamp}.json'
        
        # Calculate percentages
        total = self.stats['total']
        if total > 0:
            success_rate = (self.stats['success'] / total) * 100
            fail_rate = (self.stats['failed'] / total) * 100
        else:
            success_rate = 0
            fail_rate = 0
        
        report = {
            'timestamp': timestamp,
            'input_directory': str(self.input_dir),
            'output_directory': str(self.output_dir),
            'statistics': {
                'total_files': self.stats['total'],
                'successful': self.stats['success'],
                'failed': self.stats['failed'],
                'skipped': self.stats['skipped'],
                'success_rate': f"{success_rate:.1f}%",
                'fail_rate': f"{fail_rate:.1f}%"
            },
            'failed_files': self.stats['failed_files']
        }
        
        # Save JSON report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Log summary
        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info("PROCESSING SUMMARY")
        self.logger.info("="*60)
        self.logger.info(f"Total files:    {self.stats['total']}")
        self.logger.info(f"✓ Successful:   {self.stats['success']} ({success_rate:.1f}%)")
        self.logger.info(f"✗ Failed:       {self.stats['failed']} ({fail_rate:.1f}%)")
        self.logger.info(f"⊘ Skipped:      {self.stats['skipped']}")
        self.logger.info(f"Report saved:   {report_path}")
        self.logger.info("="*60)
        
        if self.stats['failed'] > 0:
            self.logger.warning(f"\n{self.stats['failed']} files failed to process.")
            self.logger.warning("Check the report for details.")
    
    def process_file(self, pdf_path: str, output_path: str = None) -> str:
        """
        Process a single PDF file (standalone method)
        
        Args:
            pdf_path: Path to PDF file
            output_path: Optional output path (if None, auto-generated)
            
        Returns:
            Path to output file
        """
        pdf_path = Path(pdf_path)
        
        if output_path is None:
            output_path = self.output_dir / f"{pdf_path.stem}.txt"
        else:
            output_path = Path(output_path)
        
        # Extract
        text = self.extractor.extract_pdf(str(pdf_path))
        
        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding='utf-8')
        
        return str(output_path)
