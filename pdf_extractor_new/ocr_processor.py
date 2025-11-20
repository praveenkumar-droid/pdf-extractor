"""
OCR Processor for Scanned PDFs
Extracts text from image-based PDFs using Optical Character Recognition

Supports:
- Japanese text (hiragana, katakana, kanji)
- English text
- Mixed Japanese-English documents
- Multi-engine support (EasyOCR, Tesseract)

Purpose: Handle scanned PDFs that don't have text layers
"""

import pdfplumber
from PIL import Image
import io
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


@dataclass
class OCRResult:
    """Result from OCR processing"""
    text: str
    confidence: float
    word_count: int
    char_count: int
    engine_used: str
    success: bool
    error: Optional[str] = None


class OCRProcessor:
    """
    OCR processor for extracting text from scanned PDFs.

    Features:
    - Automatic engine selection (EasyOCR preferred for Japanese)
    - Confidence scoring
    - Layout preservation
    - Multi-language support (Japanese + English)
    """

    def __init__(self,
                 languages: List[str] = ['ja', 'en'],
                 engine: str = 'auto',
                 gpu: bool = False,
                 verbose: bool = False):
        """
        Initialize OCR processor.

        Args:
            languages: List of language codes ('ja', 'en', 'zh', etc.)
            engine: OCR engine to use ('easyocr', 'tesseract', 'auto')
            gpu: Use GPU acceleration if available (EasyOCR only)
            verbose: Print detailed information
        """
        self.languages = languages
        self.engine_preference = engine
        self.gpu = gpu
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

        # Initialize OCR engine
        self.reader = None
        self.engine_used = None
        self._initialize_engine()

    def _initialize_engine(self):
        """Initialize the OCR engine"""
        # Auto-select best available engine
        if self.engine_preference == 'auto':
            if EASYOCR_AVAILABLE:
                self.engine_preference = 'easyocr'
            elif PYTESSERACT_AVAILABLE:
                self.engine_preference = 'tesseract'
            else:
                self.logger.error("No OCR engine available. Install easyocr or pytesseract.")
                return

        # Initialize selected engine
        if self.engine_preference == 'easyocr':
            if EASYOCR_AVAILABLE:
                try:
                    if self.verbose:
                        print(f"[OCR] Initializing EasyOCR for languages: {self.languages}")
                    self.reader = easyocr.Reader(
                        self.languages,
                        gpu=self.gpu,
                        verbose=False
                    )
                    self.engine_used = 'easyocr'
                    if self.verbose:
                        print(f"[OCR] EasyOCR initialized successfully")
                except Exception as e:
                    self.logger.error(f"Failed to initialize EasyOCR: {e}")
                    self.engine_used = None
            else:
                self.logger.error("EasyOCR not available. Install with: pip install easyocr")

        elif self.engine_preference == 'tesseract':
            if PYTESSERACT_AVAILABLE:
                try:
                    # Test if Tesseract is actually installed
                    pytesseract.get_tesseract_version()
                    self.engine_used = 'tesseract'
                    if self.verbose:
                        print(f"[OCR] Using Tesseract OCR")
                except Exception as e:
                    self.logger.error(f"Tesseract not properly installed: {e}")
                    self.engine_used = None
            else:
                self.logger.error("pytesseract not available. Install with: pip install pytesseract")

    def is_available(self) -> bool:
        """Check if OCR is available"""
        return self.engine_used is not None

    def process_page(self, page) -> OCRResult:
        """
        Process a single PDF page with OCR.

        Args:
            page: pdfplumber page object

        Returns:
            OCRResult with extracted text and metadata
        """
        if not self.is_available():
            return OCRResult(
                text="",
                confidence=0.0,
                word_count=0,
                char_count=0,
                engine_used="none",
                success=False,
                error="No OCR engine available"
            )

        try:
            # Convert page to image
            img = page.to_image(resolution=300).original

            # Perform OCR based on engine
            if self.engine_used == 'easyocr':
                result = self._ocr_easyocr(img)
            elif self.engine_used == 'tesseract':
                result = self._ocr_tesseract(img)
            else:
                result = OCRResult(
                    text="",
                    confidence=0.0,
                    word_count=0,
                    char_count=0,
                    engine_used="none",
                    success=False,
                    error="No engine initialized"
                )

            return result

        except Exception as e:
            self.logger.error(f"OCR processing failed: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                word_count=0,
                char_count=0,
                engine_used=self.engine_used or "unknown",
                success=False,
                error=str(e)
            )

    def _ocr_easyocr(self, img: Image.Image) -> OCRResult:
        """
        Perform OCR using EasyOCR.

        Args:
            img: PIL Image

        Returns:
            OCRResult
        """
        # Convert PIL image to format EasyOCR expects
        img_array = list(img.getdata())
        width, height = img.size

        # Run OCR
        results = self.reader.readtext(img)

        # Extract text and confidence
        text_lines = []
        confidences = []

        for detection in results:
            bbox, text, confidence = detection
            text_lines.append(text)
            confidences.append(confidence)

        # Combine results
        full_text = '\n'.join(text_lines)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return OCRResult(
            text=full_text,
            confidence=avg_confidence,
            word_count=len(text_lines),
            char_count=len(full_text),
            engine_used='easyocr',
            success=True
        )

    def _ocr_tesseract(self, img: Image.Image) -> OCRResult:
        """
        Perform OCR using Tesseract.

        Args:
            img: PIL Image

        Returns:
            OCRResult
        """
        # Configure Tesseract for Japanese
        lang_map = {'ja': 'jpn', 'en': 'eng', 'zh': 'chi_sim'}
        lang_string = '+'.join(lang_map.get(lang, 'eng') for lang in self.languages)

        # Run OCR
        text = pytesseract.image_to_string(img, lang=lang_string)

        # Get confidence data
        try:
            data = pytesseract.image_to_data(img, lang=lang_string, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if conf != '-1']
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
        except:
            avg_confidence = 0.5  # Default if confidence extraction fails

        return OCRResult(
            text=text,
            confidence=avg_confidence,
            word_count=len(text.split()),
            char_count=len(text),
            engine_used='tesseract',
            success=True
        )

    def process_pdf(self, pdf_path: str, scanned_pages: Optional[List[int]] = None) -> Dict[int, OCRResult]:
        """
        Process entire PDF or specific pages with OCR.

        Args:
            pdf_path: Path to PDF file
            scanned_pages: List of page numbers to process (1-indexed), None = all pages

        Returns:
            Dictionary mapping page numbers to OCRResults
        """
        results = {}

        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_to_process = scanned_pages or range(1, len(pdf.pages) + 1)

                for page_num in pages_to_process:
                    if self.verbose:
                        print(f"[OCR] Processing page {page_num}...")

                    page = pdf.pages[page_num - 1]
                    result = self.process_page(page)
                    results[page_num] = result

                    if self.verbose and result.success:
                        print(f"  → Extracted {result.char_count} chars (confidence: {result.confidence:.1%})")
                    elif self.verbose:
                        print(f"  → Failed: {result.error}")

        except Exception as e:
            self.logger.error(f"Failed to process PDF: {e}")

        return results

    def should_use_ocr(self, page) -> bool:
        """
        Determine if a page needs OCR (is scanned/image-based).

        Args:
            page: pdfplumber page object

        Returns:
            True if page should be processed with OCR
        """
        try:
            # Try to extract words
            words = page.extract_words()

            # If very few words, likely scanned
            if len(words) < 10:
                return True

            # If no images, definitely text-based
            images = page.images
            if not images:
                return False

            # If page is mostly image (>80%), likely scanned
            page_area = page.width * page.height
            image_area = sum(
                (img['x1'] - img['x0']) * (img['bottom'] - img['top'])
                for img in images
            )

            if image_area > page_area * 0.8:
                return True

            return False

        except Exception as e:
            self.logger.warning(f"Could not determine if OCR needed: {e}")
            return False


# Convenience functions
def extract_with_ocr(pdf_path: str,
                    languages: List[str] = ['ja', 'en'],
                    engine: str = 'auto',
                    verbose: bool = True) -> str:
    """
    Extract text from PDF with automatic OCR for scanned pages.

    Args:
        pdf_path: Path to PDF file
        languages: Languages to recognize
        engine: OCR engine preference
        verbose: Print progress

    Returns:
        Extracted text with OCR applied to scanned pages
    """
    processor = OCRProcessor(languages=languages, engine=engine, verbose=verbose)

    if not processor.is_available():
        print("⚠️ OCR not available. Install with:")
        print("   pip install easyocr")
        print("   OR")
        print("   pip install pytesseract")
        return ""

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            if verbose:
                print(f"\nProcessing page {page_num}...")

            # Check if OCR needed
            if processor.should_use_ocr(page):
                if verbose:
                    print(f"  → Scanned page detected, using OCR...")
                result = processor.process_page(page)
                if result.success:
                    results.append(f"--- Page {page_num} (OCR) ---\n{result.text}")
                else:
                    results.append(f"--- Page {page_num} (OCR FAILED) ---")
            else:
                # Regular text extraction
                if verbose:
                    print(f"  → Text-based page, using regular extraction...")
                text = page.extract_text()
                if text:
                    results.append(f"--- Page {page_num} ---\n{text}")

    return '\n\n'.join(results)


# Demo
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <pdf_path>")
        print("\nExtracts text from PDFs with automatic OCR for scanned pages.")
        print("\nRequirements:")
        print("  pip install easyocr  # Recommended for Japanese")
        print("  OR")
        print("  pip install pytesseract  # Alternative")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Check if OCR is available
    processor = OCRProcessor(languages=['ja', 'en'], verbose=True)

    if not processor.is_available():
        print("\n❌ No OCR engine available!")
        print("\nInstall one of:")
        print("  1. EasyOCR (recommended for Japanese):")
        print("     pip install easyocr")
        print("\n  2. Tesseract OCR:")
        print("     pip install pytesseract")
        print("     # Also install Tesseract binary:")
        print("     #   Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-jpn")
        print("     #   macOS: brew install tesseract tesseract-lang")
        print("     #   Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

    print(f"\nExtracting from: {pdf_path}")
    print(f"OCR Engine: {processor.engine_used}")
    print("-" * 60)

    text = extract_with_ocr(pdf_path, verbose=True)

    print("\n" + "="*60)
    print("EXTRACTED TEXT")
    print("="*60)
    print(text[:2000])  # Show first 2000 chars
    if len(text) > 2000:
        print(f"\n... ({len(text) - 2000} more characters)")

    print(f"\n\nTotal extracted: {len(text)} characters")
