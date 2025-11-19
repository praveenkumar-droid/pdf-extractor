"""
PHASE 8: ADVANCED ERROR HANDLING
Robust error handling for edge cases and corrupted content

This module handles:
1. Z-order issues (overlapping text)
2. Rotated text detection and handling
3. Corrupted/malformed content
4. Encoding fallbacks
5. Scanned/image-based page detection
6. Recovery strategies

Purpose: Gracefully handle problematic PDFs without crashing
"""

import pdfplumber
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import traceback


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"           # Informational, no action needed
    WARNING = "warning"     # Potential issue, extraction continues
    ERROR = "error"         # Significant issue, partial extraction
    CRITICAL = "critical"   # Cannot extract, needs intervention


class ErrorType(Enum):
    """Types of extraction errors"""
    ROTATION = "rotation"
    ENCODING = "encoding"
    CORRUPTION = "corruption"
    Z_ORDER = "z_order"
    SCANNED = "scanned"
    EMPTY_PAGE = "empty_page"
    MALFORMED = "malformed"
    TIMEOUT = "timeout"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass
class ExtractionError:
    """Single extraction error"""
    error_type: ErrorType
    severity: ErrorSeverity
    page_number: int
    message: str
    details: Optional[str] = None
    recovered: bool = False
    recovery_method: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'type': self.error_type.value,
            'severity': self.severity.value,
            'page': self.page_number,
            'message': self.message,
            'details': self.details,
            'recovered': self.recovered,
            'recovery_method': self.recovery_method
        }


@dataclass
class ErrorReport:
    """Complete error report for extraction"""
    total_errors: int
    errors_by_type: Dict[str, int]
    errors_by_severity: Dict[str, int]
    errors: List[ExtractionError]
    pages_affected: List[int]
    recovery_rate: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'total_errors': self.total_errors,
            'errors_by_type': self.errors_by_type,
            'errors_by_severity': self.errors_by_severity,
            'errors': [e.to_dict() for e in self.errors],
            'pages_affected': self.pages_affected,
            'recovery_rate': round(self.recovery_rate, 2),
            'recommendations': self.recommendations
        }


@dataclass
class PageAnalysis:
    """Analysis results for a single page"""
    page_number: int
    is_rotated: bool = False
    rotation_angle: int = 0
    is_scanned: bool = False
    has_text: bool = True
    has_overlapping_text: bool = False
    has_encoding_issues: bool = False
    word_count: int = 0
    char_count: int = 0
    issues: List[str] = field(default_factory=list)


class ErrorHandler:
    """
    Advanced error handler for PDF extraction.
    
    Handles:
    - Rotated pages
    - Z-order/overlapping text
    - Encoding issues
    - Scanned pages
    - Corrupted content
    - Memory issues
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize error handler.
        
        Args:
            verbose: Print detailed error information
        """
        self.verbose = verbose
        self.errors: List[ExtractionError] = []
        self.logger = logging.getLogger(__name__)
        
        # Thresholds
        self.min_words_for_text_page = 10  # Less = likely scanned
        self.overlap_threshold = 0.5  # 50% overlap = Z-order issue
        self.encoding_error_threshold = 0.05  # 5% bad chars = encoding issue
        
        # Recovery settings
        self.enable_rotation_fix = True
        self.enable_encoding_fallback = True
        self.enable_ocr_detection = True
    
    def analyze_pdf(self, pdf_path: str) -> Tuple[List[PageAnalysis], ErrorReport]:
        """
        Analyze PDF for potential issues before extraction.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (page analyses, error report)
        """
        self.errors = []  # Reset errors
        analyses = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    analysis = self._analyze_page(page, page_num)
                    analyses.append(analysis)
        except Exception as e:
            self._add_error(
                ErrorType.CORRUPTION,
                ErrorSeverity.CRITICAL,
                0,
                f"Failed to open PDF: {str(e)}",
                traceback.format_exc()
            )
        
        # Generate report
        report = self._generate_report()
        
        return analyses, report
    
    def _analyze_page(self, page, page_num: int) -> PageAnalysis:
        """Analyze a single page for issues"""
        analysis = PageAnalysis(page_number=page_num)
        
        try:
            # Check rotation
            rotation = getattr(page, 'rotation', 0) or 0
            if rotation != 0:
                analysis.is_rotated = True
                analysis.rotation_angle = rotation
                analysis.issues.append(f"Page rotated {rotation}°")
                
                self._add_error(
                    ErrorType.ROTATION,
                    ErrorSeverity.WARNING,
                    page_num,
                    f"Page is rotated {rotation}°",
                    "Text may need rotation correction"
                )
            
            # Extract words
            try:
                words = page.extract_words() or []
            except Exception as e:
                words = []
                self._add_error(
                    ErrorType.MALFORMED,
                    ErrorSeverity.ERROR,
                    page_num,
                    f"Failed to extract words: {str(e)}"
                )
            
            analysis.word_count = len(words)
            
            # Check if scanned (no/few words)
            if len(words) < self.min_words_for_text_page:
                analysis.is_scanned = True
                analysis.has_text = False
                analysis.issues.append("Possibly scanned/image-based")
                
                self._add_error(
                    ErrorType.SCANNED,
                    ErrorSeverity.WARNING,
                    page_num,
                    f"Page appears to be scanned (only {len(words)} words)",
                    "OCR may be required for full extraction"
                )
            
            # Check for overlapping text (Z-order issues)
            if words:
                overlaps = self._detect_overlapping_text(words)
                if overlaps:
                    analysis.has_overlapping_text = True
                    analysis.issues.append(f"{len(overlaps)} overlapping text regions")
                    
                    self._add_error(
                        ErrorType.Z_ORDER,
                        ErrorSeverity.WARNING,
                        page_num,
                        f"Found {len(overlaps)} overlapping text regions",
                        "May cause duplicate or jumbled text"
                    )
            
            # Check for encoding issues
            if words:
                text = ' '.join(w['text'] for w in words)
                analysis.char_count = len(text)
                
                bad_chars = self._count_encoding_errors(text)
                if bad_chars > len(text) * self.encoding_error_threshold:
                    analysis.has_encoding_issues = True
                    analysis.issues.append(f"{bad_chars} encoding errors")
                    
                    self._add_error(
                        ErrorType.ENCODING,
                        ErrorSeverity.WARNING,
                        page_num,
                        f"Found {bad_chars} encoding errors",
                        "Characters may be displayed incorrectly"
                    )
            
            # Check for empty page
            if not words:
                analysis.issues.append("Empty page")
                self._add_error(
                    ErrorType.EMPTY_PAGE,
                    ErrorSeverity.INFO,
                    page_num,
                    "Page contains no extractable text"
                )
        
        except Exception as e:
            self._add_error(
                ErrorType.UNKNOWN,
                ErrorSeverity.ERROR,
                page_num,
                f"Error analyzing page: {str(e)}",
                traceback.format_exc()
            )
        
        return analysis
    
    def _detect_overlapping_text(self, words: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Detect overlapping text elements (Z-order issues)"""
        overlaps = []
        
        for i, word1 in enumerate(words):
            for word2 in words[i+1:]:
                # Check bounding box overlap
                if self._boxes_overlap(word1, word2):
                    overlaps.append((word1, word2))
        
        return overlaps
    
    def _boxes_overlap(self, box1: Dict, box2: Dict) -> bool:
        """Check if two bounding boxes overlap significantly"""
        # Get coordinates
        x1_min, x1_max = box1['x0'], box1['x1']
        y1_min, y1_max = box1['top'], box1['bottom']
        x2_min, x2_max = box2['x0'], box2['x1']
        y2_min, y2_max = box2['top'], box2['bottom']
        
        # Calculate overlap
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        overlap_area = x_overlap * y_overlap
        
        # Calculate areas
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        
        if area1 == 0 or area2 == 0:
            return False
        
        # Check if overlap is significant
        min_area = min(area1, area2)
        return overlap_area > min_area * self.overlap_threshold
    
    def _count_encoding_errors(self, text: str) -> int:
        """Count characters that indicate encoding issues"""
        error_chars = [
            '�',  # Replacement character
            '\ufffd',  # Unicode replacement
            '\x00',  # Null
        ]
        
        count = 0
        for char in error_chars:
            count += text.count(char)
        
        # Also count suspicious patterns
        count += len(re.findall(r'\\x[0-9a-f]{2}', text))
        count += len(re.findall(r'\\u[0-9a-f]{4}', text))
        
        return count
    
    def _add_error(self, 
                   error_type: ErrorType,
                   severity: ErrorSeverity,
                   page_num: int,
                   message: str,
                   details: Optional[str] = None):
        """Add an error to the list"""
        error = ExtractionError(
            error_type=error_type,
            severity=severity,
            page_number=page_num,
            message=message,
            details=details
        )
        self.errors.append(error)
        
        if self.verbose:
            icon = "ℹ" if severity == ErrorSeverity.INFO else \
                   "⚠" if severity == ErrorSeverity.WARNING else \
                   "❌" if severity == ErrorSeverity.ERROR else "🔴"
            print(f"  {icon} Page {page_num}: {message}")
    
    def _generate_report(self) -> ErrorReport:
        """Generate comprehensive error report"""
        # Count by type
        by_type = {}
        for error in self.errors:
            type_name = error.error_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in self.errors:
            sev_name = error.severity.value
            by_severity[sev_name] = by_severity.get(sev_name, 0) + 1
        
        # Pages affected
        pages_affected = list(set(e.page_number for e in self.errors if e.page_number > 0))
        pages_affected.sort()
        
        # Recovery rate
        recovered = sum(1 for e in self.errors if e.recovered)
        recovery_rate = recovered / len(self.errors) if self.errors else 1.0
        
        # Generate recommendations
        recommendations = self._generate_recommendations(by_type, by_severity)
        
        return ErrorReport(
            total_errors=len(self.errors),
            errors_by_type=by_type,
            errors_by_severity=by_severity,
            errors=self.errors,
            pages_affected=pages_affected,
            recovery_rate=recovery_rate,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, by_type: Dict, by_severity: Dict) -> List[str]:
        """Generate recommendations based on errors found"""
        recommendations = []
        
        if by_type.get('scanned', 0) > 0:
            recommendations.append("Consider using OCR for scanned pages")
        
        if by_type.get('rotation', 0) > 0:
            recommendations.append("Enable rotation correction for rotated pages")
        
        if by_type.get('encoding', 0) > 0:
            recommendations.append("Try different encoding fallbacks (UTF-8, Shift-JIS, EUC-JP)")
        
        if by_type.get('z_order', 0) > 0:
            recommendations.append("Review overlapping text - may need manual cleanup")
        
        if by_type.get('corruption', 0) > 0:
            recommendations.append("PDF may be corrupted - try re-saving or repairing")
        
        if by_severity.get('critical', 0) > 0:
            recommendations.insert(0, "⚠️ Critical errors found - manual intervention required")
        elif by_severity.get('error', 0) > 0:
            recommendations.insert(0, "Some pages may have incomplete extraction")
        
        if not recommendations:
            recommendations.append("No significant issues found")
        
        return recommendations
    
    def handle_extraction_error(self, 
                                page, 
                                page_num: int, 
                                error: Exception) -> Tuple[str, bool]:
        """
        Handle an extraction error with recovery attempts.
        
        Args:
            page: The page object
            page_num: Page number
            error: The exception that occurred
            
        Returns:
            Tuple of (recovered_text, success)
        """
        error_str = str(error)
        
        # Try different recovery strategies
        
        # Strategy 1: Simple word extraction
        try:
            words = page.extract_words(
                x_tolerance=5,
                y_tolerance=5,
                keep_blank_chars=False
            )
            if words:
                text = ' '.join(w['text'] for w in words)
                self._mark_recovered(page_num, "simple_extraction")
                return text, True
        except:
            pass
        
        # Strategy 2: Character-by-character extraction
        try:
            chars = page.chars
            if chars:
                text = ''.join(c['text'] for c in chars)
                self._mark_recovered(page_num, "char_extraction")
                return text, True
        except:
            pass
        
        # Strategy 3: Raw text extraction
        try:
            text = page.extract_text()
            if text:
                self._mark_recovered(page_num, "raw_extraction")
                return text, True
        except:
            pass
        
        # All strategies failed
        self._add_error(
            ErrorType.CORRUPTION,
            ErrorSeverity.ERROR,
            page_num,
            f"All extraction methods failed: {error_str}",
            traceback.format_exc()
        )
        
        return f"[EXTRACTION ERROR: Page {page_num}]", False
    
    def _mark_recovered(self, page_num: int, method: str):
        """Mark errors for a page as recovered"""
        for error in self.errors:
            if error.page_number == page_num and not error.recovered:
                error.recovered = True
                error.recovery_method = method
    
    def fix_rotated_text(self, words: List[Dict], rotation: int) -> List[Dict]:
        """
        Fix coordinates for rotated text.
        
        Args:
            words: List of word dictionaries
            rotation: Rotation angle in degrees
            
        Returns:
            Words with corrected coordinates
        """
        if rotation == 0:
            return words
        
        # For now, just mark as rotated
        # Full rotation handling would require coordinate transformation
        for word in words:
            word['_rotated'] = rotation
        
        return words
    
    def fix_encoding(self, text: str) -> str:
        """
        Attempt to fix encoding issues in text.
        
        Args:
            text: Text with potential encoding issues
            
        Returns:
            Text with encoding issues fixed
        """
        # Replace common encoding errors
        replacements = {
            '�': '',  # Remove replacement characters
            '\x00': '',  # Remove nulls
            '\ufffd': '',  # Remove Unicode replacement
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Try to decode escape sequences
        try:
            # Handle \\xNN patterns
            text = re.sub(
                r'\\x([0-9a-fA-F]{2})',
                lambda m: chr(int(m.group(1), 16)),
                text
            )
        except:
            pass
        
        return text
    
    def deduplicate_overlapping(self, words: List[Dict]) -> List[Dict]:
        """
        Remove duplicate words from overlapping text.
        
        Args:
            words: List of word dictionaries
            
        Returns:
            Deduplicated words
        """
        if not words:
            return words
        
        # Sort by position
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        # Remove duplicates
        result = []
        seen_positions = set()
        
        for word in sorted_words:
            # Create position key (rounded to avoid float issues)
            pos_key = (
                round(word['x0'], 1),
                round(word['top'], 1),
                word['text']
            )
            
            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                result.append(word)
        
        return result
    
    def print_report(self, report: ErrorReport):
        """Print human-readable error report"""
        print("\n" + "="*60)
        print("ERROR HANDLING REPORT")
        print("="*60)
        
        if report.total_errors == 0:
            print("\n✅ No errors found!")
            print("="*60 + "\n")
            return
        
        print(f"\nTotal Errors: {report.total_errors}")
        print(f"Pages Affected: {len(report.pages_affected)}")
        print(f"Recovery Rate: {report.recovery_rate:.0%}")
        
        # By severity
        print("\nBy Severity:")
        severity_icons = {
            'info': 'ℹ',
            'warning': '⚠',
            'error': '❌',
            'critical': '🔴'
        }
        for sev, count in report.errors_by_severity.items():
            icon = severity_icons.get(sev, '•')
            print(f"  {icon} {sev.capitalize()}: {count}")
        
        # By type
        print("\nBy Type:")
        for error_type, count in report.errors_by_type.items():
            print(f"  • {error_type}: {count}")
        
        # Sample errors
        if report.errors:
            print("\nSample Errors:")
            for error in report.errors[:5]:
                status = "✓ Recovered" if error.recovered else "✗ Not recovered"
                print(f"  Page {error.page_number}: {error.message}")
                print(f"    Status: {status}")
                if error.recovery_method:
                    print(f"    Method: {error.recovery_method}")
        
        # Recommendations
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  → {rec}")
        
        print("="*60 + "\n")


class SafeExtractor:
    """
    Wrapper for safe extraction with error handling.
    
    Wraps any extractor and adds error handling capabilities.
    """
    
    def __init__(self, extractor, verbose: bool = True):
        """
        Initialize safe extractor.
        
        Args:
            extractor: The base extractor to wrap
            verbose: Print error information
        """
        self.extractor = extractor
        self.error_handler = ErrorHandler(verbose=verbose)
        self.verbose = verbose
    
    def extract_safe(self, pdf_path: str) -> Tuple[str, ErrorReport]:
        """
        Extract PDF with full error handling.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, error_report)
        """
        # First, analyze the PDF
        if self.verbose:
            print("\n[Error Handler] Analyzing PDF for issues...")
        
        analyses, pre_report = self.error_handler.analyze_pdf(pdf_path)
        
        if self.verbose:
            if pre_report.total_errors > 0:
                print(f"  → Found {pre_report.total_errors} potential issues")
            else:
                print("  → No issues detected")
        
        # Attempt extraction
        try:
            text = self.extractor.extract_pdf(pdf_path)
            
            # Post-process based on analysis
            for analysis in analyses:
                if analysis.has_encoding_issues:
                    # Fix encoding in the relevant section
                    text = self.error_handler.fix_encoding(text)
            
            # Generate final report
            final_report = self.error_handler._generate_report()
            
            return text, final_report
            
        except Exception as e:
            # Critical extraction failure
            self.error_handler._add_error(
                ErrorType.CORRUPTION,
                ErrorSeverity.CRITICAL,
                0,
                f"Extraction failed: {str(e)}",
                traceback.format_exc()
            )
            
            final_report = self.error_handler._generate_report()
            
            return f"[EXTRACTION FAILED: {str(e)}]", final_report


# Convenience functions
def analyze_pdf_errors(pdf_path: str, verbose: bool = True) -> ErrorReport:
    """
    Analyze a PDF for potential extraction issues.
    
    Args:
        pdf_path: Path to PDF file
        verbose: Print detailed information
        
    Returns:
        ErrorReport with all issues found
    """
    handler = ErrorHandler(verbose=verbose)
    analyses, report = handler.analyze_pdf(pdf_path)
    
    if verbose:
        handler.print_report(report)
    
    return report


def extract_with_error_handling(pdf_path: str, 
                                extractor=None,
                                verbose: bool = True) -> Tuple[str, ErrorReport]:
    """
    Extract PDF with comprehensive error handling.
    
    Args:
        pdf_path: Path to PDF file
        extractor: Extractor to use (defaults to JapanesePDFExtractor)
        verbose: Print detailed information
        
    Returns:
        Tuple of (extracted_text, error_report)
    """
    if extractor is None:
        from extractor import JapanesePDFExtractor
        extractor = JapanesePDFExtractor()
    
    safe = SafeExtractor(extractor, verbose=verbose)
    return safe.extract_safe(pdf_path)


# Demo
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python error_handler.py <pdf_path>")
        print("\nAnalyzes PDF for potential extraction issues.")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    print(f"\nAnalyzing: {pdf_path}")
    print("-" * 40)
    
    # Analyze
    report = analyze_pdf_errors(pdf_path, verbose=True)
    
    # Try extraction with error handling
    if report.total_errors > 0:
        print("\nAttempting extraction with error handling...")
        text, final_report = extract_with_error_handling(pdf_path, verbose=True)
        
        print(f"\nExtracted {len(text)} characters")
        print(f"Recovery rate: {final_report.recovery_rate:.0%}")
