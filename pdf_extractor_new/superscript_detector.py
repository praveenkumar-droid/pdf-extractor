"""
PHASE 1: SUPERSCRIPT/SUBSCRIPT DETECTION
Enhanced text analysis with font-based detection

This module detects superscripts and subscripts by analyzing:
- Font size relative to surrounding text
- Baseline offset (vertical position)
- Common patterns (H₂O, x², *1, etc.)

Purpose: Capture chemical formulas, math expressions, and footnote markers
"""
import pdfplumber
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import re


@dataclass
class EnhancedTextElement:
    """
    Text element with enhanced attributes for super/subscript detection
    """
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    height: float
    
    # Font attributes
    fontname: str = ""
    size: float = 0.0
    
    # Calculated attributes
    is_superscript: bool = False
    is_subscript: bool = False
    baseline_offset: float = 0.0
    relative_size: float = 1.0
    
    # Context
    preceding_text: str = ""
    following_text: str = ""
    
    def __repr__(self):
        script_type = ""
        if self.is_superscript:
            script_type = " [SUP]"
        elif self.is_subscript:
            script_type = " [SUB]"
        return f"'{self.text}'{script_type} @({self.x0:.1f}, {self.top:.1f})"


class SuperscriptSubscriptDetector:
    """
    Detects superscripts and subscripts in PDF text.
    
    Uses multiple detection methods:
    1. Font size analysis (relative to neighbors)
    2. Baseline offset detection
    3. Pattern matching (common formulas)
    4. Height-based detection (fallback)
    """
    
    def __init__(self):
        # Detection thresholds
        self.size_threshold = 0.7        # < 70% of avg = super/subscript
        self.baseline_threshold = 0.20   # > 20% offset = super/subscript
        self.min_superscript_size = 4    # Minimum pt size to consider
        self.max_superscript_size = 10   # Maximum pt size for super/sub
        
        # Common superscript/subscript patterns
        self.superscript_patterns = [
            r'^\d+$',           # Numbers: 1, 2, 3
            r'^\*\d+$',         # Asterisk: *1, *2
            r'^[¹²³⁴⁵⁶⁷⁸⁹⁰]+$', # Unicode superscripts
            r'^[ⁱⁿᵃᵇᶜᵈᵉᶠᵍʰʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ]+$',  # Superscript letters
        ]
        
        self.subscript_patterns = [
            r'^\d+$',           # Numbers: 1, 2, 3
            r'^[₀₁₂₃₄₅₆₇₈₉]+$', # Unicode subscripts
            r'^[ₐₑᵢₒᵤ]+$',      # Subscript letters
        ]
        
        # Chemical formula patterns (for context)
        self.chemical_patterns = [
            r'H\d+',   # H2, H2O
            r'O\d+',   # O2, O3
            r'C\d+',   # C6, CH4
            r'N\d+',   # N2, NH3
            r'Ca\d+',  # Ca2+
            r'Na\d+',  # Na+
        ]
        
        # Math patterns
        self.math_patterns = [
            r'[a-z]\d+',  # x2, y3
            r'[A-Z]\d+',  # X2, Y3
        ]
    
    def analyze_page(self, page) -> List[EnhancedTextElement]:
        """
        Analyze a page and detect all superscripts/subscripts.
        
        Args:
            page: pdfplumber page object
            
        Returns:
            List of EnhancedTextElement with super/subscript flags set
        """
        # Extract words with detailed attributes
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            extra_attrs=['fontname', 'size']
        )
        
        if not words:
            return []
        
        # Convert to EnhancedTextElement
        elements = []
        for word in words:
            element = EnhancedTextElement(
                text=word.get('text', ''),
                x0=word.get('x0', 0),
                top=word.get('top', 0),
                x1=word.get('x1', 0),
                bottom=word.get('bottom', 0),
                height=word.get('height', 10),
                fontname=word.get('fontname', ''),
                size=word.get('size', 0.0)
            )
            elements.append(element)
        
        # Sort by position (top to bottom, left to right)
        elements.sort(key=lambda e: (e.top, e.x0))
        
        # Calculate average font size for reference
        avg_size = self._calculate_average_size(elements)
        
        # Detect superscripts and subscripts
        for i, element in enumerate(elements):
            # Get surrounding elements for context
            prev_element = elements[i-1] if i > 0 else None
            next_element = elements[i+1] if i < len(elements) - 1 else None
            
            # Store context
            if prev_element:
                element.preceding_text = prev_element.text
            if next_element:
                element.following_text = next_element.text
            
            # Detect super/subscript
            self._detect_script_type(element, prev_element, next_element, avg_size)
        
        return elements
    
    def _calculate_average_size(self, elements: List[EnhancedTextElement]) -> float:
        """Calculate average font size, excluding outliers"""
        sizes = [e.size for e in elements if e.size > 0]
        if not sizes:
            # Fallback to height
            sizes = [e.height for e in elements if e.height > 0]
        
        if not sizes:
            return 12.0  # Default fallback
        
        # Remove outliers (top/bottom 10%)
        sizes.sort()
        trim = len(sizes) // 10
        if trim > 0:
            sizes = sizes[trim:-trim]
        
        return sum(sizes) / len(sizes) if sizes else 12.0
    
    def _detect_script_type(self, 
                           element: EnhancedTextElement,
                           prev_element: Optional[EnhancedTextElement],
                           next_element: Optional[EnhancedTextElement],
                           avg_size: float):
        """
        Detect if element is superscript or subscript.
        
        Uses multiple detection methods:
        1. Font size analysis
        2. Baseline offset
        3. Pattern matching
        4. Context awareness
        """
        # Skip if no size information
        if element.size == 0 and element.height == 0:
            return
        
        # Use size if available, otherwise height
        element_size = element.size if element.size > 0 else element.height
        
        # METHOD 1: Size-based detection
        element.relative_size = element_size / avg_size if avg_size > 0 else 1.0
        is_small = element.relative_size < self.size_threshold
        
        # METHOD 2: Baseline offset detection
        if prev_element and prev_element.size > 0:
            # Calculate baseline offset relative to previous element
            baseline_diff = element.top - prev_element.top
            ref_height = prev_element.size if prev_element.size > 0 else prev_element.height
            
            if ref_height > 0:
                element.baseline_offset = baseline_diff / ref_height
        
        # METHOD 3: Pattern matching
        is_superscript_pattern = any(
            re.match(pattern, element.text) 
            for pattern in self.superscript_patterns
        )
        is_subscript_pattern = any(
            re.match(pattern, element.text) 
            for pattern in self.subscript_patterns
        )
        
        # METHOD 4: Context awareness
        has_chemical_context = False
        has_math_context = False
        
        if prev_element:
            combined = prev_element.text + element.text
            has_chemical_context = any(
                re.search(pattern, combined) 
                for pattern in self.chemical_patterns
            )
            has_math_context = any(
                re.search(pattern, combined) 
                for pattern in self.math_patterns
            )
        
        # DECISION LOGIC
        # Superscript if:
        # - Small AND raised baseline OR
        # - Matches superscript pattern OR
        # - After asterisk/dagger markers
        if is_small and (
            element.baseline_offset > self.baseline_threshold or
            is_superscript_pattern or
            (prev_element and prev_element.text in ['*', '†', '‡', '※'])
        ):
            element.is_superscript = True
            return
        
        # Subscript if:
        # - Small AND lowered baseline OR
        # - Matches subscript pattern OR
        # - Has chemical/math context
        if is_small and (
            element.baseline_offset < -self.baseline_threshold or
            is_subscript_pattern or
            (has_chemical_context or has_math_context)
        ):
            element.is_subscript = True
            return
        
        # SPECIAL CASES
        
        # Footnote markers: *1, *2, etc.
        if element.text.startswith('*') and element.text[1:].isdigit():
            if is_small or element_size < self.max_superscript_size:
                element.is_superscript = True
                return
        
        # Reference numbers: [1], [2], etc.
        if re.match(r'^\[\d+\]$', element.text):
            if is_small or element_size < self.max_superscript_size:
                element.is_superscript = True
                return
        
        # Unicode super/subscript characters
        if re.search(r'[¹²³⁴⁵⁶⁷⁸⁹⁰₀₁₂₃₄₅₆₇₈₉]', element.text):
            if any(c in '¹²³⁴⁵⁶⁷⁸⁹⁰' for c in element.text):
                element.is_superscript = True
            elif any(c in '₀₁₂₃₄₅₆₇₈₉' for c in element.text):
                element.is_subscript = True
    
    def get_statistics(self, elements: List[EnhancedTextElement]) -> Dict[str, int]:
        """Get statistics about detected super/subscripts"""
        stats = {
            'total': len(elements),
            'superscripts': sum(1 for e in elements if e.is_superscript),
            'subscripts': sum(1 for e in elements if e.is_subscript),
            'normal': sum(1 for e in elements if not e.is_superscript and not e.is_subscript)
        }
        
        stats['superscript_percent'] = (
            stats['superscripts'] / stats['total'] * 100 
            if stats['total'] > 0 else 0
        )
        stats['subscript_percent'] = (
            stats['subscripts'] / stats['total'] * 100 
            if stats['total'] > 0 else 0
        )
        
        return stats
    
    def print_statistics(self, stats: Dict[str, int]):
        """Print human-readable statistics"""
        print("\n" + "="*60)
        print("SUPERSCRIPT/SUBSCRIPT DETECTION STATISTICS")
        print("="*60)
        print(f"Total elements:    {stats['total']:,}")
        print(f"Superscripts:      {stats['superscripts']:,} ({stats['superscript_percent']:.1f}%)")
        print(f"Subscripts:        {stats['subscripts']:,} ({stats['subscript_percent']:.1f}%)")
        print(f"Normal text:       {stats['normal']:,}")
        print("="*60 + "\n")
    
    def extract_with_markup(self, elements: List[EnhancedTextElement]) -> str:
        """
        Extract text with super/subscript markup for debugging.
        
        Format:
        - Superscripts: text^{super}
        - Subscripts: text_{sub}
        """
        result = []
        
        for element in elements:
            if element.is_superscript:
                result.append(f"^{{{element.text}}}")
            elif element.is_subscript:
                result.append(f"_{{{element.text}}}")
            else:
                result.append(element.text)
        
        return ' '.join(result)
    
    def find_formulas(self, elements: List[EnhancedTextElement]) -> List[str]:
        """
        Find chemical/mathematical formulas.
        
        Returns list of detected formulas with their super/subscripts.
        """
        formulas = []
        i = 0
        
        while i < len(elements):
            element = elements[i]
            
            # Check if starts a formula
            if element.text in ['H', 'O', 'C', 'N', 'Ca', 'Na', 'CO', 'H2', 'NH']:
                formula_parts = [element.text]
                j = i + 1
                
                # Collect following subscripts/superscripts
                while j < len(elements):
                    next_elem = elements[j]
                    
                    # Stop if too far away horizontally
                    if next_elem.x0 - elements[j-1].x1 > 5:
                        break
                    
                    # Add if it's a subscript/superscript or a letter
                    if (next_elem.is_subscript or 
                        next_elem.is_superscript or 
                        next_elem.text.isalpha()):
                        formula_parts.append(next_elem.text)
                        j += 1
                    else:
                        break
                
                if len(formula_parts) > 1:
                    formulas.append(''.join(formula_parts))
                    i = j
                else:
                    i += 1
            else:
                i += 1
        
        return formulas


# Convenience function
def analyze_pdf_scripts(pdf_path: str) -> Dict[int, List[EnhancedTextElement]]:
    """
    Quick function to analyze all pages for super/subscripts.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary mapping page_number to list of EnhancedTextElement
    """
    detector = SuperscriptSubscriptDetector()
    results = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            elements = detector.analyze_page(page)
            results[page_num] = elements
            
            # Print stats for each page
            stats = detector.get_statistics(elements)
            if stats['superscripts'] > 0 or stats['subscripts'] > 0:
                print(f"\nPage {page_num}: {stats['superscripts']} superscripts, "
                      f"{stats['subscripts']} subscripts")
    
    return results
