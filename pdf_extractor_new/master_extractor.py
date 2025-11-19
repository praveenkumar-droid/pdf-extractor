"""
MASTER EXTRACTOR - ALL PHASES INTEGRATED (WEEK 1 + WEEK 2)
Complete PDF extraction with all improvements

This module integrates:
- Phase 0: Element Inventory (completeness verification)
- Phase 1: Superscript/Subscript Detection
- Phase 2: Layout Intelligence (tables, text boxes)
- Phase 3: Smart Extraction Rules (section numbers, footnote markers)
- Phase 4: Character Preservation (no transformation)
- Phase 5: LLM Verification (OCR error correction)
- Phase 6: Footnote System (markers + definitions)
- Phase 7: Quality Scoring (A-F grade)
- Phase 9: Page Markers (professional formatting)

Usage:
    from master_extractor import MasterExtractor
    
    extractor = MasterExtractor()
    result = extractor.extract("input/document.pdf")
    
    # result contains:
    # - formatted_text: Complete output with page markers
    # - raw_text: Text without formatting
    # - quality_report: Quality grade and scores
    # - footnotes: Extracted footnotes
    # - tables: Extracted tables
"""

import pdfplumber
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

# Import all phase modules
from extractor import JapanesePDFExtractor
from element_inventory import ElementInventoryAnalyzer
from superscript_detector import SuperscriptSubscriptDetector
from layout_analyzer import LayoutAnalyzer
from footnote_extractor import FootnoteExtractor
from llm_verifier import LLMVerifier
from quality_scorer import QualityScorer
from output_formatter import OutputFormatter
from error_handler import ErrorHandler, SafeExtractor
from context_windows import LargeDocumentProcessor, ChunkingStrategy
from flagging_system import FlaggingSystem, FlagType, FlagSeverity


@dataclass
class ExtractionResult:
    """Complete extraction result with all data"""
    formatted_text: str          # Text with page markers
    raw_text: str                # Text without markers
    pages: List[str]             # Individual page texts
    
    # Verification data
    inventory_report: Dict[str, Any]
    footnote_report: Dict[str, Any]
    quality_report: Dict[str, Any]
    
    # Extracted elements
    footnotes: List[Dict]
    tables: List[Dict]
    textboxes: List[Dict]
    superscripts: List[Dict]
    subscripts: List[Dict]
    
    # LLM verification
    llm_corrections: int
    
    # Error handling
    error_report: Dict[str, Any]
    
    # Chunking info (for large documents)
    chunks_used: int
    was_chunked: bool
    
    # Metadata
    filename: str
    page_count: int
    word_count: int
    extraction_time: float
    quality_grade: str
    
    def __repr__(self):
        return (f"ExtractionResult(pages={self.page_count}, "
                f"words={self.word_count}, "
                f"grade={self.quality_grade}, "
                f"time={self.extraction_time:.2f}s)")


class MasterExtractor:
    """
    Master extractor that integrates all phases (Week 1 + Week 2).
    
    Features:
    - Pre-extraction element counting (Phase 0)
    - Superscript/subscript detection (Phase 1)
    - Table and text box extraction (Phase 2)
    - Smart filtering with section/footnote preservation (Phase 3)
    - Character preservation - no transformation (Phase 4)
    - LLM verification for OCR errors (Phase 5)
    - Complete footnote extraction (Phase 6)
    - Quality scoring with A-F grade (Phase 7)
    - Professional output formatting (Phase 9)
    """
    
    def __init__(self, 
                 verbose: bool = True,
                 enable_llm_verification: bool = False,
                 llm_backend: str = "mock",
                 llm_api_key: Optional[str] = None,
                 max_chunk_size: int = 100000,
                 enable_chunking: bool = True):
        """
        Initialize master extractor.
        
        Args:
            verbose: Print progress messages
            enable_llm_verification: Enable LLM-based error correction
            llm_backend: LLM backend ("mock", "openai", "anthropic", "local")
            llm_api_key: API key for LLM service
            max_chunk_size: Maximum characters per chunk for large documents
            enable_chunking: Enable chunking for large documents
        """
        self.verbose = verbose
        self.enable_llm_verification = enable_llm_verification
        self.max_chunk_size = max_chunk_size
        self.enable_chunking = enable_chunking
        
        # Initialize all components
        self.text_extractor = JapanesePDFExtractor()
        self.inventory_analyzer = ElementInventoryAnalyzer()
        self.script_detector = SuperscriptSubscriptDetector()
        self.layout_analyzer = LayoutAnalyzer()
        self.footnote_extractor = FootnoteExtractor()
        self.quality_scorer = QualityScorer()
        self.output_formatter = OutputFormatter()
        
        # Initialize LLM verifier
        self.llm_verifier = LLMVerifier(
            llm_backend=llm_backend,
            api_key=llm_api_key
        )
        
        # Initialize error handler (Phase 8)
        self.error_handler = ErrorHandler(verbose=verbose)
        
        # Initialize large document processor (Phase 10)
        chunking_strategy = ChunkingStrategy(
            max_chunk_size=max_chunk_size,
            overlap_size=500,
            preserve_sections=True,
            preserve_paragraphs=True
        )
        self.large_doc_processor = LargeDocumentProcessor(
            strategy=chunking_strategy,
            verbose=verbose
        )
        
        # Configure output formatter
        self.output_formatter.add_statistics = True
        self.output_formatter.add_timestamp = True
    
    def extract(self, pdf_path: str) -> ExtractionResult:
        """
        Extract text from PDF using all phases.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with complete data
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"MASTER EXTRACTION: {Path(pdf_path).name}")
            print(f"{'='*60}")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 8: PRE-ANALYSIS ERROR DETECTION
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 8] Analyzing PDF for potential issues...")
        
        page_analyses, error_report_obj = self.error_handler.analyze_pdf(pdf_path)
        
        if self.verbose:
            if error_report_obj.total_errors > 0:
                print(f"  → Found {error_report_obj.total_errors} potential issues")
                for err_type, count in error_report_obj.errors_by_type.items():
                    print(f"    • {err_type}: {count}")
            else:
                print("  → No issues detected")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 0: CREATE ELEMENT INVENTORY
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 0] Creating element inventory...")
        
        inventories = self.inventory_analyzer.analyze_pdf(pdf_path)
        
        total_elements = sum(inv.total_elements for inv in inventories.values())
        if self.verbose:
            print(f"  → Found {total_elements:,} elements across {len(inventories)} pages")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 1: DETECT SUPERSCRIPTS/SUBSCRIPTS
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 1] Detecting superscripts/subscripts...")
        
        all_superscripts = []
        all_subscripts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                elements = self.script_detector.analyze_page(page)
                
                for elem in elements:
                    if elem.is_superscript:
                        all_superscripts.append({
                            'text': elem.text,
                            'page': page_num,
                            'x': elem.x0,
                            'y': elem.top
                        })
                    elif elem.is_subscript:
                        all_subscripts.append({
                            'text': elem.text,
                            'page': page_num,
                            'x': elem.x0,
                            'y': elem.top
                        })
        
        if self.verbose:
            print(f"  → Found {len(all_superscripts)} superscripts, {len(all_subscripts)} subscripts")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 2: ANALYZE LAYOUT (TABLES, TEXT BOXES)
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 2] Analyzing page layouts...")
        
        all_tables = []
        all_textboxes = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                regions = self.layout_analyzer.analyze_page(page, page_num)
                
                for region in regions:
                    if region.region_type == "table":
                        table = region.content
                        all_tables.append({
                            'page': page_num,
                            'rows': table.rows,
                            'cols': table.cols,
                            'text': table.to_text(),
                            'has_header': table.has_header
                        })
                    elif region.region_type == "textbox":
                        textbox = region.content
                        all_textboxes.append({
                            'page': page_num,
                            'type': textbox.box_type,
                            'text': textbox.text
                        })
        
        if self.verbose:
            print(f"  → Found {len(all_tables)} tables, {len(all_textboxes)} text boxes")
        
        # ═══════════════════════════════════════════════════════════
        # PHASES 3 & 4: EXTRACT TEXT WITH SMART FILTERING
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 3+4] Extracting text with smart filtering...")
        
        # Get pages as list (with error handling)
        pages = self._extract_pages_safe(pdf_path, page_analyses)
        raw_text = '\n\n'.join(pages)
        
        if self.verbose:
            print(f"  → Extracted {len(pages)} pages, {len(raw_text.split()):,} words")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 5: LLM VERIFICATION (OPTIONAL)
        # ═══════════════════════════════════════════════════════════
        llm_corrections = 0
        
        if self.enable_llm_verification:
            if self.verbose:
                print("\n[Phase 5] Running LLM verification...")
            
            corrected_text, verification_report = self.llm_verifier.verify_text(raw_text)
            llm_corrections = verification_report.total_corrections_made
            
            if llm_corrections > 0:
                raw_text = corrected_text
                # Re-split into pages (approximate)
                # Note: This is simplified; ideally track corrections per page
                pages = raw_text.split('\n\n')
            
            if self.verbose:
                print(f"  → Made {llm_corrections} corrections")
                print(f"  → Avg confidence: {verification_report.average_confidence:.2f}")
        else:
            if self.verbose:
                print("\n[Phase 5] LLM verification: SKIPPED (disabled)")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 6: EXTRACT FOOTNOTES
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 6] Extracting footnotes...")
        
        all_footnotes_data = self.footnote_extractor.extract_footnotes_from_pdf(pdf_path)
        
        # Collect all footnotes
        all_markers = []
        all_definitions = []
        all_matches = []
        
        for page_num, (markers, definitions) in all_footnotes_data.items():
            all_markers.extend(markers)
            all_definitions.extend(definitions)
            
            # Match on this page
            matches = self.footnote_extractor.match_markers_to_definitions(markers, definitions)
            all_matches.extend(matches)
        
        # Verify footnotes
        footnote_report = self.footnote_extractor.verify_completeness(
            all_markers, all_definitions, all_matches
        )
        
        if self.verbose:
            print(f"  → Found {len(all_markers)} markers, {len(all_definitions)} definitions")
            print(f"  → Match rate: {footnote_report['match_rate']}%")
        
        # Convert to simple dict format
        footnotes_list = []
        for defn in all_definitions:
            footnotes_list.append({
                'marker': defn.marker,
                'text': defn.text,
                'page': defn.page_number
            })
        
        # ═══════════════════════════════════════════════════════════
        # INTEGRATE TEXTBOXES AND FOOTNOTES INTO PAGES
        # NOTE: Tables are now handled by extractor.py to prevent duplication
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Integration] Adding text boxes and footnotes to pages...")

        pages_with_content = []
        for page_num, page_text in enumerate(pages, 1):
            # NOTE: Tables are NO LONGER appended here - they're integrated
            # during extraction in extractor.py to prevent duplication

            # Add text boxes for this page
            page_boxes = [b for b in all_textboxes if b['page'] == page_num]
            for box in page_boxes:
                if box['type'] == 'warning':
                    page_text += f"\n\n[WARNING BOX]\n{box['text']}\n[WARNING BOX END]"
                elif box['type'] == 'note':
                    page_text += f"\n\n[NOTE BOX]\n{box['text']}\n[NOTE BOX END]"
                else:
                    page_text += f"\n\n[{box['type'].upper()} BOX]\n{box['text']}\n[{box['type'].upper()} BOX END]"

            # Add footnotes for this page
            page_footnotes = [fn for fn in footnotes_list if fn['page'] == page_num]
            if page_footnotes:
                page_text += "\n\n" + "─"*40 + "\n"
                page_text += "FOOTNOTES:\n"
                for fn in page_footnotes:
                    page_text += f"{fn['marker']}: {fn['text']}\n"

            pages_with_content.append(page_text)
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 9: FORMAT OUTPUT WITH PAGE MARKERS
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 9] Formatting output with page markers...")
        
        filename = Path(pdf_path).name
        
        # Create metadata
        metadata = {
            'page_count': len(pages),
            'word_count': len(raw_text.split()),
            'char_count': len(raw_text),
            'extraction_method': 'MasterExtractor (All Phases)',
            'superscripts': len(all_superscripts),
            'subscripts': len(all_subscripts),
            'footnotes': len(all_definitions),
            'tables': len(all_tables),
            'textboxes': len(all_textboxes),
            'llm_corrections': llm_corrections,
            'errors_found': error_report_obj.total_errors,
            'recovery_rate': f"{error_report_obj.recovery_rate:.0%}"
        }
        
        # Format with markers
        formatted_text = self.output_formatter.format_document(
            pages_with_content, 
            filename, 
            metadata
        )
        
        if self.verbose:
            print(f"  → Formatted {len(formatted_text):,} characters")
        
        # ═══════════════════════════════════════════════════════════
        # VERIFY EXTRACTION COMPLETENESS
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Verification] Checking extraction completeness...")
        
        inventory_report = self.inventory_analyzer.verify_extraction(
            inventories, raw_text, len(pages)
        )
        
        if self.verbose:
            status_icon = "✓" if inventory_report['status'] == 'GOOD' else "⚠" if inventory_report['status'] == 'WARNING' else "✗"
            print(f"  → Coverage: {inventory_report['coverage_percent']:.1f}% ({status_icon} {inventory_report['status']})")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 7: QUALITY SCORING
        # ═══════════════════════════════════════════════════════════
        if self.verbose:
            print("\n[Phase 7] Scoring extraction quality...")
        
        quality_report_obj = self.quality_scorer.score_extraction(
            extracted_text=raw_text,
            inventory_report=inventory_report,
            footnote_report=footnote_report,
            table_count=len(all_tables),
            page_count=len(pages)
        )
        
        quality_report = quality_report_obj.to_dict()
        quality_grade = quality_report['grade']
        
        if self.verbose:
            grade_icon = "🟢" if quality_grade in ["Excellent", "Good"] else "🟡" if quality_grade == "Acceptable" else "🔴"
            print(f"  → Grade: {grade_icon} {quality_grade} ({quality_report['overall_score']:.1f}/100)")
        
        # ═══════════════════════════════════════════════════════════
        # CREATE RESULT
        # ═══════════════════════════════════════════════════════════
        extraction_time = time.time() - start_time
        
        result = ExtractionResult(
            formatted_text=formatted_text,
            raw_text=raw_text,
            pages=pages_with_content,
            inventory_report=inventory_report,
            footnote_report=footnote_report,
            quality_report=quality_report,
            footnotes=footnotes_list,
            tables=all_tables,
            textboxes=all_textboxes,
            superscripts=all_superscripts,
            subscripts=all_subscripts,
            llm_corrections=llm_corrections,
            error_report=error_report_obj.to_dict(),
            chunks_used=1,  # Single chunk for standard extraction
            was_chunked=False,
            filename=filename,
            page_count=len(pages),
            word_count=len(raw_text.split()),
            extraction_time=extraction_time,
            quality_grade=quality_grade
        )
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"EXTRACTION COMPLETE")
            print(f"{'='*60}")
            print(f"Pages: {result.page_count}")
            print(f"Words: {result.word_count:,}")
            print(f"Tables: {len(all_tables)}")
            print(f"Footnotes: {len(footnotes_list)}")
            print(f"Quality: {quality_grade} ({quality_report['overall_score']:.1f}/100)")
            print(f"Errors: {error_report_obj.total_errors} (Recovery: {error_report_obj.recovery_rate:.0%})")
            print(f"Time: {result.extraction_time:.2f}s")
            print(f"{'='*60}\n")
        
        return result
    
    def _extract_pages_safe(self, pdf_path: str, page_analyses: list) -> List[str]:
        """
        Extract text as list of pages with error handling.
        
        Uses the main extractor but handles errors gracefully.
        
        Args:
            pdf_path: Path to PDF file
            page_analyses: Pre-analysis results from error handler
        """
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Detect repeating elements
            try:
                headers, footers = self.text_extractor._detect_repeating_elements(pdf)
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠ Warning: Could not detect headers/footers: {e}")
                headers, footers = [], []
            
            # Extract each page
            for page_num, page in enumerate(pdf.pages, 1):
                # Get analysis for this page
                analysis = page_analyses[page_num - 1] if page_num <= len(page_analyses) else None
                
                try:
                    # Check for known issues
                    if analysis and analysis.is_scanned:
                        # Scanned page - may have limited text
                        page_text = f"[SCANNED PAGE {page_num} - Limited text extraction]"
                        try:
                            extracted = self.text_extractor._extract_page(page, headers, footers)
                            if extracted.strip():
                                page_text = extracted
                        except:
                            pass
                    else:
                        # Normal extraction
                        page_text = self.text_extractor._extract_page(page, headers, footers)
                    
                    # Apply cleanup if we have text
                    if page_text.strip() and not page_text.startswith("["):
                        import config
                        if config.FIX_SPACING or config.JOIN_LINES or config.FIX_PUNCTUATION:
                            page_text = self.text_extractor._cleanup_text(page_text)
                        
                        # Fix encoding issues if detected
                        if analysis and analysis.has_encoding_issues:
                            page_text = self.error_handler.fix_encoding(page_text)
                    
                    pages.append(page_text if page_text.strip() else "")
                    
                except Exception as e:
                    # Handle extraction error
                    if self.verbose:
                        print(f"  ⚠ Error on page {page_num}: {e}")
                    
                    # Try recovery
                    recovered_text, success = self.error_handler.handle_extraction_error(
                        page, page_num, e
                    )
                    
                    if success:
                        pages.append(recovered_text)
                    else:
                        pages.append(f"[EXTRACTION ERROR: Page {page_num}]")
        
        return pages
    
    def _extract_pages(self, pdf_path: str) -> List[str]:
        """
        Extract text as list of pages (legacy method without error handling).
        
        Uses the main extractor but returns pages separately.
        """
        pages = []
        
        with pdfplumber.open(pdf_path) as pdf:
            # Detect repeating elements
            headers, footers = self.text_extractor._detect_repeating_elements(pdf)
            
            # Extract each page
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = self.text_extractor._extract_page(page, headers, footers)
                
                if page_text.strip():
                    # Apply cleanup
                    import config
                    if config.FIX_SPACING or config.JOIN_LINES or config.FIX_PUNCTUATION:
                        page_text = self.text_extractor._cleanup_text(page_text)
                    
                    pages.append(page_text)
                else:
                    pages.append("")  # Keep empty pages for numbering
        
        return pages
    
    def extract_to_file(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract PDF and save to file.
        
        Args:
            pdf_path: Input PDF path
            output_path: Output text path (auto-generated if not provided)
            
        Returns:
            Path to output file
        """
        # Extract
        result = self.extract(pdf_path)
        
        # Determine output path
        if output_path is None:
            pdf_file = Path(pdf_path)
            output_path = str(pdf_file.with_suffix('.txt'))
        
        # Save
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.formatted_text)
        
        if self.verbose:
            print(f"Saved to: {output_path}")
        
        return output_path
    
    def extract_large_document(self, pdf_path: str) -> ExtractionResult:
        """
        Extract a large PDF document using chunking.
        
        This method is optimized for documents that are too large
        to process in a single pass. It:
        1. Chunks the document into manageable pieces
        2. Processes each chunk with context preservation
        3. Reassembles with deduplication
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with complete data
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"LARGE DOCUMENT EXTRACTION: {Path(pdf_path).name}")
            print(f"{'='*60}")
        
        # First, do the standard extraction to get pages
        if self.verbose:
            print("\n[Phase 10] Extracting pages for chunking...")
        
        # Quick page extraction without all phases
        pages = self._extract_pages(pdf_path)
        total_chars = sum(len(p) for p in pages)
        
        if self.verbose:
            print(f"  → Extracted {len(pages)} pages, {total_chars:,} characters")
        
        # Check if chunking is needed
        if total_chars <= self.max_chunk_size:
            if self.verbose:
                print(f"  → Document size ({total_chars:,}) within limit ({self.max_chunk_size:,})")
                print(f"  → Using standard extraction")
            return self.extract(pdf_path)
        
        # Chunk the document
        if self.verbose:
            print(f"\n[Phase 10] Chunking large document...")
        
        chunks = self.large_doc_processor.chunk_document(pages, Path(pdf_path).name)
        
        if self.verbose:
            print(f"  → Created {len(chunks)} chunks")
            print(f"  → Memory estimate: {self.large_doc_processor.estimate_memory_usage(pages)['total_mb']} MB")
        
        # Process each chunk
        if self.verbose:
            print(f"\n[Phase 10] Processing chunks...")
        
        processed_results = []
        all_tables = []
        all_textboxes = []
        all_footnotes = []
        all_superscripts = []
        all_subscripts = []
        total_llm_corrections = 0
        
        for chunk in chunks:
            if self.verbose:
                print(f"  Processing chunk {chunk.chunk_id + 1}/{len(chunks)} "
                      f"(pages {chunk.page_start}-{chunk.page_end})...")
            
            # Get pages for this chunk
            chunk_pages = pages[chunk.page_start - 1:chunk.page_end]
            
            # Analyze layout for chunk pages
            with pdfplumber.open(pdf_path) as pdf:
                for i, page_num in enumerate(range(chunk.page_start, chunk.page_end + 1)):
                    if page_num <= len(pdf.pages):
                        page = pdf.pages[page_num - 1]
                        
                        # Layout analysis
                        regions = self.layout_analyzer.analyze_page(page, page_num)
                        for region in regions:
                            if region.region_type == "table":
                                table = region.content
                                all_tables.append({
                                    'page': page_num,
                                    'rows': table.rows,
                                    'cols': table.cols,
                                    'text': table.to_text(),
                                    'has_header': table.has_header
                                })
                            elif region.region_type == "textbox":
                                textbox = region.content
                                all_textboxes.append({
                                    'page': page_num,
                                    'type': textbox.box_type,
                                    'text': textbox.text
                                })
                        
                        # Script detection
                        elements = self.script_detector.analyze_page(page)
                        for elem in elements:
                            if elem.is_superscript:
                                all_superscripts.append({
                                    'text': elem.text,
                                    'page': page_num,
                                    'x': elem.x0,
                                    'y': elem.top
                                })
                            elif elem.is_subscript:
                                all_subscripts.append({
                                    'text': elem.text,
                                    'page': page_num,
                                    'x': elem.x0,
                                    'y': elem.top
                                })
            
            # LLM verification on chunk if enabled
            chunk_text = chunk.content
            if self.enable_llm_verification:
                corrected, report = self.llm_verifier.verify_text(chunk_text)
                chunk_text = corrected
                total_llm_corrections += report.total_corrections_made
            
            processed_results.append(chunk_text)
        
        # Reassemble chunks
        if self.verbose:
            print(f"\n[Phase 10] Reassembling {len(chunks)} chunks...")
        
        reassembly = self.large_doc_processor.reassemble_chunks(chunks, processed_results)
        raw_text = reassembly.full_text
        
        if self.verbose:
            print(f"  → Duplicates removed: {reassembly.duplicates_removed}")
            print(f"  → Final word count: {reassembly.total_words:,}")
        
        # Extract footnotes
        if self.verbose:
            print(f"\n[Phase 6] Extracting footnotes...")
        
        all_footnotes_data = self.footnote_extractor.extract_footnotes_from_pdf(pdf_path)
        all_markers = []
        all_definitions = []
        all_matches = []
        
        for page_num, (markers, definitions) in all_footnotes_data.items():
            all_markers.extend(markers)
            all_definitions.extend(definitions)
            matches = self.footnote_extractor.match_markers_to_definitions(markers, definitions)
            all_matches.extend(matches)
        
        footnote_report = self.footnote_extractor.verify_completeness(
            all_markers, all_definitions, all_matches
        )
        
        footnotes_list = [{'marker': d.marker, 'text': d.text, 'page': d.page_number} 
                         for d in all_definitions]
        
        # Create inventory report
        inventories = self.inventory_analyzer.analyze_pdf(pdf_path)
        inventory_report = self.inventory_analyzer.verify_extraction(
            inventories, raw_text, len(pages)
        )
        
        # Quality scoring
        quality_report_obj = self.quality_scorer.score_extraction(
            extracted_text=raw_text,
            inventory_report=inventory_report,
            footnote_report=footnote_report,
            table_count=len(all_tables),
            page_count=len(pages)
        )
        quality_report = quality_report_obj.to_dict()
        
        # Format output
        if self.verbose:
            print(f"\n[Phase 9] Formatting output...")
        
        # Split raw_text back into pages for formatting
        pages_with_content = raw_text.split('\n\n')
        
        filename = Path(pdf_path).name
        metadata = {
            'page_count': len(pages),
            'word_count': reassembly.total_words,
            'char_count': len(raw_text),
            'extraction_method': 'MasterExtractor (Chunked)',
            'chunks_used': len(chunks),
            'tables': len(all_tables),
            'footnotes': len(all_definitions),
            'llm_corrections': total_llm_corrections
        }
        
        formatted_text = self.output_formatter.format_document(
            pages, filename, metadata
        )
        
        extraction_time = time.time() - start_time
        
        # Create result
        result = ExtractionResult(
            formatted_text=formatted_text,
            raw_text=raw_text,
            pages=pages,
            inventory_report=inventory_report,
            footnote_report=footnote_report,
            quality_report=quality_report,
            footnotes=footnotes_list,
            tables=all_tables,
            textboxes=all_textboxes,
            superscripts=all_superscripts,
            subscripts=all_subscripts,
            llm_corrections=total_llm_corrections,
            error_report={'total_errors': 0, 'recovery_rate': 1.0, 'errors_by_type': {}, 'pages_affected': [], 'recommendations': []},
            chunks_used=len(chunks),
            was_chunked=True,
            filename=filename,
            page_count=len(pages),
            word_count=reassembly.total_words,
            extraction_time=extraction_time,
            quality_grade=quality_report['grade']
        )
        
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"LARGE DOCUMENT EXTRACTION COMPLETE")
            print(f"{'='*60}")
            print(f"Pages: {result.page_count}")
            print(f"Words: {result.word_count:,}")
            print(f"Chunks: {len(chunks)}")
            print(f"Tables: {len(all_tables)}")
            print(f"Quality: {quality_report['grade']}")
            print(f"Time: {extraction_time:.2f}s")
            print(f"{'='*60}\n")
        
        return result
    
    def print_quality_report(self, result: ExtractionResult):
        """Print detailed quality report"""
        self.quality_scorer.print_report(
            # Reconstruct QualityReport from dict
            type('QualityReport', (), {
                'overall_score': result.quality_report['overall_score'],
                'grade': type('Grade', (), {'name': result.quality_grade, 'value': result.quality_grade})(),
                'confidence': result.quality_report['confidence'],
                'dimensions': [
                    type('Dim', (), {'name': k, 'score': v['score'], 'issues': v['issues']})()
                    for k, v in result.quality_report['dimensions'].items()
                ],
                'issues': result.quality_report['issues'],
                'recommendations': result.quality_report['recommendations']
            })()
        )
    
    def print_report(self, result: ExtractionResult):
        """Print detailed extraction report"""
        print("\n" + "="*60)
        print("DETAILED EXTRACTION REPORT")
        print("="*60)
        
        # Basic info
        print(f"\nFile: {result.filename}")
        print(f"Pages: {result.page_count}")
        print(f"Words: {result.word_count:,}")
        print(f"Time: {result.extraction_time:.2f}s")
        
        # Quality
        print(f"\n--- QUALITY GRADE ---")
        print(f"Grade: {result.quality_grade}")
        print(f"Score: {result.quality_report['overall_score']:.1f}/100")
        print(f"Confidence: {result.quality_report['confidence']:.0%}")
        
        # Inventory report
        print(f"\n--- ELEMENT INVENTORY ---")
        inv = result.inventory_report
        print(f"Total expected: {inv['total_expected']:,}")
        print(f"Total extracted: {inv['total_extracted']:,}")
        print(f"Coverage: {inv['coverage_percent']:.1f}%")
        print(f"Status: {inv['status']}")
        
        # Layout elements
        print(f"\n--- LAYOUT ELEMENTS ---")
        print(f"Tables: {len(result.tables)}")
        print(f"Text boxes: {len(result.textboxes)}")
        print(f"Superscripts: {len(result.superscripts)}")
        print(f"Subscripts: {len(result.subscripts)}")
        
        # Footnote report
        print(f"\n--- FOOTNOTES ---")
        fn = result.footnote_report
        print(f"Markers found: {fn['total_markers']}")
        print(f"Definitions found: {fn['total_definitions']}")
        print(f"Matched: {fn['total_matches']}")
        print(f"Match rate: {fn['match_rate']}%")
        
        # LLM verification
        print(f"\n--- LLM VERIFICATION ---")
        print(f"Corrections made: {result.llm_corrections}")
        
        # Error handling (Phase 8)
        print(f"\n--- ERROR HANDLING ---")
        err = result.error_report
        print(f"Total errors: {err['total_errors']}")
        print(f"Recovery rate: {err['recovery_rate']:.0%}")
        if err['pages_affected']:
            print(f"Pages affected: {', '.join(map(str, err['pages_affected'][:10]))}")
            if len(err['pages_affected']) > 10:
                print(f"  ... and {len(err['pages_affected']) - 10} more")
        
        if err['errors_by_type']:
            print("By type:")
            for err_type, count in err['errors_by_type'].items():
                print(f"  • {err_type}: {count}")
        
        # Recommendations
        if result.quality_report.get('recommendations'):
            print(f"\n--- RECOMMENDATIONS ---")
            for rec in result.quality_report['recommendations'][:5]:
                print(f"  → {rec}")
        
        print("="*60 + "\n")


# Convenience function
def extract_pdf(pdf_path: str, 
                verbose: bool = True,
                enable_llm: bool = False) -> ExtractionResult:
    """
    Quick function to extract PDF with all phases.
    
    Args:
        pdf_path: Path to PDF file
        verbose: Print progress messages
        enable_llm: Enable LLM verification
        
    Returns:
        ExtractionResult
    """
    extractor = MasterExtractor(
        verbose=verbose,
        enable_llm_verification=enable_llm
    )
    return extractor.extract(pdf_path)


# CLI support
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python master_extractor.py <pdf_path> [output_path] [--llm]")
        print("\nExample:")
        print("  python master_extractor.py input/document.pdf")
        print("  python master_extractor.py input/document.pdf output/result.txt")
        print("  python master_extractor.py input/document.pdf --llm")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = None
    enable_llm = False
    
    for arg in sys.argv[2:]:
        if arg == "--llm":
            enable_llm = True
        elif not arg.startswith("--"):
            output_path = arg
    
    # Extract
    extractor = MasterExtractor(
        verbose=True,
        enable_llm_verification=enable_llm
    )
    
    result = extractor.extract(pdf_path)
    extractor.print_report(result)
    
    # Save
    if output_path:
        extractor.extract_to_file(pdf_path, output_path)
    else:
        output_file = extractor.extract_to_file(pdf_path)
        print(f"\nOutput saved to: {output_file}")
