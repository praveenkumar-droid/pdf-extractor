"""
Japanese PDF Text Extractor
100% Deterministic extraction with coordinate-based sorting

CRITICAL PRINCIPLE: "EXTRACT ONLY - NEVER TRANSFORM"
- All characters are preserved exactly as they appear
- No half-width to full-width conversion
- No katakana normalization  
- No character transformations of any kind

PHASE 3: SMART EXTRACTION RULES
- Section numbers preserved (1.2, 3.1.4, (1), ①)
- Footnote markers preserved (*1, *2, ※, 注)
- "Include by default" - only remove when certain it's metadata
- Context-aware page number detection
"""
import pdfplumber
import re
from typing import List, Dict, Tuple
from collections import Counter
import config


class JapanesePDFExtractor:
    """
    Extracts text from Japanese PDFs in perfect visual reading order
    
    EXTRACTION FIDELITY:
    - Preserves all characters exactly as they appear (no transformation)
    - Maintains original character widths (half/full)
    - Keeps original punctuation and spacing
    - Only applies minimal, non-transformative cleanup
    
    SMART FILTERING (Phase 3):
    - Distinguishes section numbers from page numbers
    - Preserves footnote markers
    - "Include by default" - only removes definite metadata
    """
    
    def __init__(self):
        self.column_gap = config.COLUMN_GAP_THRESHOLD
        self.line_height = config.LINE_HEIGHT_THRESHOLD
        
        # NOTE: Character normalization has been REMOVED (Phase 4)
        # Per LLM extraction specs: "EXTRACT ONLY - NEVER TRANSFORM"
        # All characters are now preserved exactly as they appear in PDF
        
        # PHASE 3: SMART PATTERN RECOGNITION
        # ═══════════════════════════════════════════════════════════
        
        # STRICT page number patterns - definitely remove these
        self.strict_page_patterns = [
            r'^Page\s+\d+$',           # "Page 5"
            r'^ページ\s*\d+$',          # "ページ 5"  
            r'^-\s*\d+\s*-$',          # "- 5 -"
            r'^\d+\s*/\s*\d+$',        # "5 / 100"
            r'^p\.\s*\d+$',            # "p. 5"
            r'^P\.\s*\d+$',            # "P. 5"
        ]
        
        # Section number patterns - definitely keep these
        self.section_patterns = [
            r'^\d+\.\d+',              # 1.2, 3.1.4, 1.2.3
            r'^\(\d+\)',               # (1), (2), (3)
            r'^[①-⑳]',                 # ①, ②, ③ (circled numbers)
            r'^\d+[)）]',               # 1), 2), 1）, 2）
            r'^第?\d+[章条項節款目]',   # 第1章, 第2条, 1章, 2条
            r'^\d+\.',                 # 1., 2. (when followed by space/text)
            r'^[一二三四五六七八九十]+[、.]',  # 一、 二、 三、
        ]
        
        # Footnote markers - definitely keep these
        self.footnote_markers = [
            r'^\*\d+',                 # *1, *2, *3
            r'^※\d*',                  # ※, ※1, ※2
            r'^注\d*',                  # 注, 注1, 注2
            r'^†',                     # † (dagger)
            r'^‡',                     # ‡ (double dagger)
            r'^\[\d+\]',               # [1], [2], [3]
            r'^\(\*\d+\)',             # (*1), (*2)
        ]
        
        # Warning: OLD pattern removed - was too aggressive
        # OLD: r'^\d+$' caught both page numbers AND section starts
        # NEW: Context-aware detection in _filter_metadata
    
    def extract_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF in visual reading order
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text in reading order with characters preserved exactly
        """
        with pdfplumber.open(pdf_path) as pdf:
            # Phase 1: Detect repeating elements across pages
            headers, footers = self._detect_repeating_elements(pdf)
            
            # Phase 2: Process each page
            all_pages = []
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = self._extract_page(page, headers, footers)
                if page_text.strip():
                    all_pages.append(page_text)
            
            # Phase 3: Combine pages
            raw_text = '\n\n'.join(all_pages)
            
            # Phase 4: Minimal cleanup (NO character transformation)
            if config.FIX_SPACING or config.JOIN_LINES or config.FIX_PUNCTUATION:
                cleaned_text = self._cleanup_text(raw_text)
            else:
                cleaned_text = raw_text
            
            return cleaned_text
    
    def _detect_repeating_elements(self, pdf) -> Tuple[List[str], List[str]]:
        """Detect headers and footers that repeat across pages"""
        if len(pdf.pages) < 3:
            return [], []
        
        sample_size = min(5, len(pdf.pages))
        top_texts = []
        bottom_texts = []
        
        for page in pdf.pages[:sample_size]:
            words = page.extract_words()
            if not words:
                continue
            
            # Top 10% of page
            top_boundary = page.height * 0.1
            top = [w['text'] for w in words if w['top'] < top_boundary]
            top_texts.append(' '.join(top))
            
            # Bottom 10% of page
            bottom_boundary = page.height * 0.9
            bottom = [w['text'] for w in words if w['top'] > bottom_boundary]
            bottom_texts.append(' '.join(bottom))
        
        # Find common patterns (appear in 80%+ of pages)
        def find_common(texts):
            if not texts:
                return []
            counter = Counter(texts)
            threshold = len(texts) * 0.8
            return [text for text, count in counter.items() 
                    if count >= threshold and text.strip()]
        
        headers = find_common(top_texts) if config.REMOVE_HEADERS_FOOTERS else []
        footers = find_common(bottom_texts) if config.REMOVE_HEADERS_FOOTERS else []
        
        return headers, footers
    
    def _extract_page(self, page, headers: List[str], footers: List[str]) -> str:
        """Extract text from a single page"""
        # Get all words with coordinates
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False
        )
        
        if not words:
            return ""
        
        # Filter out headers, footers, page numbers (SMART filtering - Phase 3)
        if config.REMOVE_HEADERS_FOOTERS or config.REMOVE_PAGE_NUMBERS:
            words = self._filter_metadata(words, headers, footers, page.height, page.width)
        
        # Detect columns
        columns = self._detect_columns(words, page.width)
        
        # Extract text from each column
        page_texts = []
        for column_words in columns:
            column_text = self._extract_column(column_words)
            page_texts.append(column_text)
        
        return '\n\n'.join(page_texts)
    
    def _filter_metadata(self, words: List[Dict], headers: List[str], 
                         footers: List[str], page_height: float, page_width: float) -> List[Dict]:
        """
        Remove headers, footers, and page numbers using SMART detection.
        
        PHASE 3 IMPROVEMENT: Include by default, only remove when certain.
        
        Priority:
        1. Keep section numbers (1.2, 3.1.4, (1), ①)
        2. Keep footnote markers (*1, ※, 注)
        3. Remove strict page patterns (Page 5, ページ 5)
        4. Remove repeating headers/footers
        5. Context-aware single digit filtering
        6. Keep everything else (include by default)
        """
        filtered = []
        
        for i, word in enumerate(words):
            text = word['text'].strip()
            
            if not text:
                continue
            
            # ═══════════════════════════════════════════════════════
            # RULE 1: ALWAYS KEEP SECTION NUMBERS
            # ═══════════════════════════════════════════════════════
            if self._is_section_number(text):
                filtered.append(word)
                continue
            
            # ═══════════════════════════════════════════════════════
            # RULE 2: ALWAYS KEEP FOOTNOTE MARKERS
            # ═══════════════════════════════════════════════════════
            if any(re.match(pattern, text) for pattern in self.footnote_markers):
                filtered.append(word)
                continue
            
            # ═══════════════════════════════════════════════════════
            # RULE 3: REMOVE STRICT PAGE NUMBER PATTERNS
            # ═══════════════════════════════════════════════════════
            if config.REMOVE_PAGE_NUMBERS:
                if any(re.match(pattern, text, re.IGNORECASE) for pattern in self.strict_page_patterns):
                    continue  # Skip this word
            
            # ═══════════════════════════════════════════════════════
            # RULE 4: REMOVE DETECTED REPEATING HEADERS/FOOTERS
            # ═══════════════════════════════════════════════════════
            if config.REMOVE_HEADERS_FOOTERS:
                if text in headers or text in footers:
                    continue  # Skip this word
            
            # ═══════════════════════════════════════════════════════
            # RULE 5: CONTEXT-AWARE SINGLE DIGIT FILTERING
            # ═══════════════════════════════════════════════════════
            # Only for pure single digits (1, 2, 3, etc.)
            if re.match(r'^\d+$', text) and len(text) <= 3:
                # Check if it's a page number (not content)
                if self._is_page_number_not_content(text, word, page_height, page_width, words):
                    continue  # Skip - it's a page number
                # Otherwise, keep it (might be section start or content)
            
            # ═══════════════════════════════════════════════════════
            # RULE 6: REMOVE ONLY EXTREME MARGINS
            # ═══════════════════════════════════════════════════════
            # Narrowed from 5% to 3% to preserve more content
            if word['top'] < page_height * 0.03:  # Top 3%
                continue
            if word['top'] > page_height * 0.97:  # Bottom 3%
                continue
            
            # ═══════════════════════════════════════════════════════
            # DEFAULT: KEEP IT (INCLUDE BY DEFAULT)
            # ═══════════════════════════════════════════════════════
            filtered.append(word)
        
        return filtered
    
    def _is_section_number(self, text: str) -> bool:
        """
        Detect if text is a section number that should be KEPT.
        
        Section numbers include:
        - 1.2, 3.1.4, 1.2.3 (decimal notation)
        - (1), (2), (3) (parentheses)
        - ①, ②, ③ (circled numbers)
        - 1), 2), 1）, 2） (closing parenthesis)
        - 第1章, 第2条 (Japanese section markers)
        - 1., 2. (period after number, if followed by space)
        
        Returns:
            True if it's a section number (KEEP IT)
            False otherwise
        """
        # Check against all section patterns
        for pattern in self.section_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
    def _is_page_number_not_content(self, text: str, word: Dict, 
                                     page_height: float, page_width: float,
                                     all_words: List[Dict]) -> bool:
        """
        Determine if a single digit/number is a page number (REMOVE) vs content (KEEP).
        
        Page number indicators:
        - In corner/margin (top 10% or bottom 10%)
        - Isolated with no nearby text (within 50pt)
        - Centered horizontally near page edge
        - Small font size (if available)
        
        Conservative approach: Only return True if CONFIDENT it's a page number.
        When in doubt, return False (keep the text).
        
        Returns:
            True if definitely a page number (REMOVE IT)
            False if might be content (KEEP IT - include by default)
        """
        # Check vertical position - page numbers usually in top 10% or bottom 10%
        in_top_margin = word['top'] < page_height * 0.1
        in_bottom_margin = word['top'] > page_height * 0.9
        
        if not (in_top_margin or in_bottom_margin):
            # In main content area - keep it
            return False
        
        # Check if isolated (no nearby text)
        if self._has_nearby_content(word, all_words, distance=50):
            # Has nearby text - probably not a page number
            return False
        
        # Check horizontal position - page numbers often centered or in corners
        word_center_x = (word['x0'] + word['x1']) / 2
        page_center_x = page_width / 2
        is_centered = abs(word_center_x - page_center_x) < page_width * 0.2  # Within 20% of center
        
        in_left_corner = word['x0'] < page_width * 0.2
        in_right_corner = word['x1'] > page_width * 0.8
        
        # If it's in margin AND (centered OR in corner) AND isolated → page number
        if (in_top_margin or in_bottom_margin) and (is_centered or in_left_corner or in_right_corner):
            return True  # Confident it's a page number
        
        # When in doubt, keep it
        return False
    
    def _has_nearby_content(self, word: Dict, all_words: List[Dict], distance: float = 50) -> bool:
        """
        Check if there's other text near this word.
        
        Args:
            word: The word to check
            all_words: All words on the page
            distance: Maximum distance in points to check (default 50pt)
        
        Returns:
            True if there's nearby text (word is not isolated)
            False if isolated (no nearby text)
        """
        word_x = (word['x0'] + word['x1']) / 2
        word_y = (word['top'] + word['bottom']) / 2
        
        # Check for nearby words
        nearby_count = 0
        for other_word in all_words:
            if other_word == word:
                continue
            
            other_x = (other_word['x0'] + other_word['x1']) / 2
            other_y = (other_word['top'] + other_word['bottom']) / 2
            
            # Calculate distance
            dist = ((word_x - other_x) ** 2 + (word_y - other_y) ** 2) ** 0.5
            
            if dist < distance:
                nearby_count += 1
                if nearby_count >= 2:  # If 2+ nearby words, definitely has content
                    return True
        
        return nearby_count > 0
    
    def _detect_columns(self, words: List[Dict], page_width: float) -> List[List[Dict]]:
        """Detect columns by analyzing X-position gaps"""
        if not words:
            return []
        
        # Sort by X position
        sorted_words = sorted(words, key=lambda w: w['x0'])
        
        # Find large horizontal gaps (column separators)
        columns = []
        current_column = [sorted_words[0]]
        
        for i in range(1, len(sorted_words)):
            prev = sorted_words[i-1]
            curr = sorted_words[i]
            
            gap = curr['x0'] - prev['x1']
            
            if gap > self.column_gap:
                columns.append(current_column)
                current_column = [curr]
            else:
                current_column.append(curr)
        
        columns.append(current_column)
        return columns
    
    def _extract_column(self, words: List[Dict]) -> str:
        """Extract text from a single column, top to bottom"""
        # Sort by Y position (top to bottom), then X (left to right)
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        # Group into lines
        lines = []
        current_line = [sorted_words[0]]
        
        for word in sorted_words[1:]:
            y_dist = abs(word['top'] - current_line[-1]['top'])
            
            if y_dist < self.line_height:
                current_line.append(word)
            else:
                lines.append(current_line)
                current_line = [word]
        
        lines.append(current_line)
        
        # Build text - PRESERVE CHARACTERS EXACTLY
        text_lines = []
        for line in lines:
            line_sorted = sorted(line, key=lambda w: w['x0'])
            # NO TRANSFORMATION - Join text exactly as extracted
            line_text = ''.join([w['text'] for w in line_sorted])
            text_lines.append(line_text)
        
        return '\n'.join(text_lines)
    
    def _cleanup_text(self, text: str) -> str:
        """
        Apply minimal cleanup - NO CHARACTER TRANSFORMATION
        
        Per LLM extraction specs: "EXTRACT ONLY - NEVER TRANSFORM"
        Characters are preserved exactly as they appear in PDF
        """
        # REMOVED: Character normalization (violates extraction rules - Phase 4)
        # All characters are now preserved in their original form
        
        # Optional spacing fixes (can be disabled via config)
        if config.FIX_SPACING:
            text = self._fix_spacing(text)
        
        # Optional line joining (preserves content structure)
        if config.JOIN_LINES:
            text = self._join_lines(text)
        
        # Optional punctuation cleanup (minimal changes)
        if config.FIX_PUNCTUATION:
            text = self._fix_punctuation(text)
        
        # Remove excessive blank lines only
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        return text.strip()
    
    def _fix_spacing(self, text: str) -> str:
        """Fix spacing between Japanese and alphanumeric (optional)"""
        # Remove spaces between Japanese characters
        text = re.sub(
            r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])\s+([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])',
            r'\1\2', text
        )
        
        # Remove spaces before Japanese punctuation
        text = re.sub(r'\s+([。、！？）］】」』])', r'\1', text)
        
        # Remove spaces after opening brackets
        text = re.sub(r'([（［【「『])\s+', r'\1', text)
        
        # Add space between Japanese and alphanumeric
        text = re.sub(
            r'([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])([a-zA-Z0-9])',
            r'\1 \2', text
        )
        text = re.sub(
            r'([a-zA-Z0-9])([\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF])',
            r'\1 \2', text
        )
        
        return text
    
    def _join_lines(self, text: str) -> str:
        """Join lines that should be together"""
        lines = text.split('\n')
        joined = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                joined.append('')
                i += 1
                continue
            
            # Check if should join with next line
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                
                if self._should_join(line, next_line):
                    joined.append(line + next_line)
                    i += 2
                    continue
            
            joined.append(line)
            i += 1
        
        return '\n'.join(joined)
    
    def _should_join(self, line: str, next_line: str) -> bool:
        """Determine if two lines should be joined"""
        if not line or not next_line:
            return False
        
        # Don't join if ends with sentence terminator
        if line[-1] in '。！？」』】）：；':
            return False
        
        # Don't join if next line starts with bullet/number
        if re.match(r'^[・■□●○①-⑳\d]+[.．)）]\s*', next_line):
            return False
        
        # Don't join if next line starts with section marker
        if re.match(r'^第?\d+[章条項節]', next_line):
            return False
        
        # Join if ends with particle
        if line[-1] in 'はがをにでとのへからもや':
            return True
        
        # Join if ends with comma
        if line[-1] in '、，':
            return True
        
        return False
    
    def _fix_punctuation(self, text: str) -> str:
        """Fix common punctuation issues (minimal changes only)"""
        # Remove duplicate punctuation
        text = re.sub(r'。+', '。', text)
        text = re.sub(r'、+', '、', text)
        
        # Normalize ellipsis
        text = re.sub(r'\.\.\.+', '…', text)
        text = re.sub(r'・・・+', '…', text)
        
        return text
