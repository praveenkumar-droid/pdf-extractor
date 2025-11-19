"""
PHASE 6: FOOTNOTE SYSTEM
Complete footnote handling with marker-definition matching

This module:
1. Detects footnote markers in main text (*1, ※, 注)
2. Extracts footnote definitions at page bottom
3. Matches markers with definitions
4. Verifies completeness (all markers have definitions)

Purpose: Preserve complete footnote content and structure
"""
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FootnoteMarker:
    """A footnote marker in the main text"""
    marker: str           # The marker text (e.g., "*1", "※", "注1")
    page_number: int      # Page where marker appears
    x: float             # X coordinate
    y: float             # Y coordinate
    context: str         # Surrounding text for reference
    
    def __repr__(self):
        return f"Marker('{self.marker}' on page {self.page_number} at y={self.y:.1f})"


@dataclass
class FootnoteDefinition:
    """A footnote definition (usually at page bottom)"""
    marker: str           # The marker (e.g., "*1")
    text: str            # The definition text
    page_number: int     # Page where definition appears
    y: float            # Y coordinate (for verification)
    
    def __repr__(self):
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Definition('{self.marker}': '{preview}' on page {self.page_number})"


@dataclass
class FootnoteMatch:
    """A matched marker-definition pair"""
    marker: FootnoteMarker
    definition: FootnoteDefinition
    confidence: float    # 0.0 to 1.0
    
    def __repr__(self):
        return f"Match('{self.marker.marker}' → definition on page {self.definition.page_number})"


class FootnoteExtractor:
    """
    Extracts and matches footnotes from PDF pages.
    
    Handles various footnote styles:
    - Asterisk: *1, *2, *3
    - Japanese: ※, ※1, 注, 注1, 注2
    - Daggers: †, ‡
    - Numbers: [1], [2], (1), (2)
    - Superscripts: ¹, ², ³
    """
    
    def __init__(self):
        # Footnote marker patterns
        self.marker_patterns = [
            # Asterisk style
            (r'\*\d+', 'asterisk'),           # *1, *2, *3
            (r'\*(?=[^\d]|$)', 'asterisk'),   # * (alone)
            
            # Japanese style
            (r'※\d*', 'kome'),                # ※, ※1, ※2
            (r'注\d*', 'chu'),                # 注, 注1, 注2
            
            # Dagger style
            (r'†', 'dagger'),                 # †
            (r'‡', 'double_dagger'),          # ‡
            
            # Bracketed style
            (r'\[\d+\]', 'bracketed'),        # [1], [2]
            (r'\(\d+\)', 'parenthesized'),    # (1), (2)
            
            # Superscript numbers (unicode)
            (r'[¹²³⁴⁵⁶⁷⁸⁹⁰]+', 'unicode_super'),
        ]
        
        # Definition start patterns (how footnotes begin at page bottom)
        self.definition_patterns = [
            r'^\*\d+[\s:：]',        # *1: or *1 
            r'^\*[\s:：]',           # * 
            r'^※\d*[\s:：]',         # ※1: or ※
            r'^注\d*[\s:：]',        # 注1: or 注
            r'^†[\s:：]',            # †:
            r'^‡[\s:：]',            # ‡:
            r'^\[\d+\][\s:：]',      # [1]:
            r'^\(\d+\)[\s:：]',      # (1):
            r'^[¹²³⁴⁵⁶⁷⁸⁹⁰]+[\s:：]', # ¹:
        ]
        
        # Region boundaries
        self.footnote_region_threshold = 0.80  # Bottom 20% of page
        self.footnote_max_height = 0.20        # Footnotes in bottom 20%
    
    def extract_footnotes_from_pdf(self, pdf_path: str) -> Dict[int, Tuple[List[FootnoteMarker], List[FootnoteDefinition]]]:
        """
        Extract all footnotes from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page_number to (markers, definitions)
        """
        results = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                markers, definitions = self._extract_page_footnotes(page, page_num)
                results[page_num] = (markers, definitions)
        
        return results
    
    def _extract_page_footnotes(self, page, page_num: int) -> Tuple[List[FootnoteMarker], List[FootnoteDefinition]]:
        """
        Extract footnotes from a single page.
        
        Returns:
            Tuple of (markers_in_text, definitions_at_bottom)
        """
        # Get all text with coordinates
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False
        )
        
        if not words:
            return [], []
        
        page_height = page.height
        footnote_boundary = page_height * self.footnote_region_threshold
        
        # Separate into main content and footnote region
        main_words = []
        footnote_words = []
        
        for word in words:
            if word['top'] < footnote_boundary:
                main_words.append(word)
            else:
                footnote_words.append(word)
        
        # Extract markers from main content
        markers = self._find_markers(main_words, page_num, page_height)
        
        # Extract definitions from footnote region
        definitions = self._find_definitions(footnote_words, page_num)
        
        return markers, definitions
    
    def _find_markers(self, words: List[Dict], page_num: int, page_height: float) -> List[FootnoteMarker]:
        """Find footnote markers in main text"""
        markers = []
        
        for i, word in enumerate(words):
            text = word['text'].strip()
            
            # Check against all marker patterns
            for pattern, marker_type in self.marker_patterns:
                if re.match(pattern, text):
                    # Get context (surrounding words)
                    context_before = []
                    context_after = []
                    
                    # Get 3 words before
                    for j in range(max(0, i-3), i):
                        context_before.append(words[j]['text'])
                    
                    # Get 3 words after
                    for j in range(i+1, min(len(words), i+4)):
                        context_after.append(words[j]['text'])
                    
                    context = ' '.join(context_before) + f" [{text}] " + ' '.join(context_after)
                    
                    marker = FootnoteMarker(
                        marker=text,
                        page_number=page_num,
                        x=word['x0'],
                        y=word['top'],
                        context=context
                    )
                    markers.append(marker)
                    break  # Don't check other patterns
        
        return markers
    
    def _find_definitions(self, words: List[Dict], page_num: int) -> List[FootnoteDefinition]:
        """
        Find footnote definitions in footnote region.
        
        Definitions typically start with a marker followed by text.
        """
        if not words:
            return []
        
        definitions = []
        
        # Sort words by position (top to bottom, left to right)
        sorted_words = sorted(words, key=lambda w: (w['top'], w['x0']))
        
        # Group into lines
        lines = self._group_into_lines(sorted_words)
        
        # Process each line to find definition starts
        i = 0
        while i < len(lines):
            line = lines[i]
            line_text = ' '.join([w['text'] for w in line])
            
            # Check if line starts with a definition pattern
            matched_marker = None
            for pattern in self.definition_patterns:
                match = re.match(pattern, line_text)
                if match:
                    # Extract the marker part
                    matched_marker = match.group().rstrip(':：').strip()
                    break
            
            if matched_marker:
                # Found a definition start
                # Extract the definition text (may span multiple lines)
                definition_parts = [line_text]
                j = i + 1
                
                # Continue to next lines until we hit another definition or end
                while j < len(lines):
                    next_line = lines[j]
                    next_line_text = ' '.join([w['text'] for w in next_line])
                    
                    # Check if next line starts a new definition
                    is_new_definition = any(
                        re.match(pattern, next_line_text) 
                        for pattern in self.definition_patterns
                    )
                    
                    if is_new_definition:
                        break
                    
                    definition_parts.append(next_line_text)
                    j += 1
                
                # Combine all parts
                full_text = ' '.join(definition_parts)
                
                # Remove the marker from the beginning of text
                definition_text = re.sub(r'^' + re.escape(matched_marker) + r'[\s:：]*', '', full_text).strip()
                
                definition = FootnoteDefinition(
                    marker=matched_marker,
                    text=definition_text,
                    page_number=page_num,
                    y=line[0]['top'] if line else 0
                )
                definitions.append(definition)
                
                # Skip the lines we processed
                i = j
            else:
                i += 1
        
        return definitions
    
    def _group_into_lines(self, words: List[Dict], tolerance: float = 5.0) -> List[List[Dict]]:
        """Group words into lines based on Y coordinate"""
        if not words:
            return []
        
        lines = []
        current_line = [words[0]]
        
        for word in words[1:]:
            # Check if on same line (similar Y coordinate)
            if abs(word['top'] - current_line[0]['top']) < tolerance:
                current_line.append(word)
            else:
                # Sort current line by X coordinate
                current_line.sort(key=lambda w: w['x0'])
                lines.append(current_line)
                current_line = [word]
        
        # Add last line
        if current_line:
            current_line.sort(key=lambda w: w['x0'])
            lines.append(current_line)
        
        return lines
    
    def match_markers_to_definitions(self, 
                                    markers: List[FootnoteMarker],
                                    definitions: List[FootnoteDefinition]) -> List[FootnoteMatch]:
        """
        Match footnote markers with their definitions.
        
        Uses fuzzy matching to handle slight variations.
        """
        matches = []
        matched_definitions = set()
        
        for marker in markers:
            best_match = None
            best_confidence = 0.0
            
            for definition in definitions:
                if definition in matched_definitions:
                    continue
                
                # Calculate match confidence
                confidence = self._calculate_match_confidence(marker, definition)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = definition
            
            # If we found a good match (>0.5 confidence)
            if best_match and best_confidence > 0.5:
                match = FootnoteMatch(
                    marker=marker,
                    definition=best_match,
                    confidence=best_confidence
                )
                matches.append(match)
                matched_definitions.add(best_match)
        
        return matches
    
    def _calculate_match_confidence(self, 
                                   marker: FootnoteMarker,
                                   definition: FootnoteDefinition) -> float:
        """
        Calculate confidence that a marker matches a definition.
        
        Returns:
            Confidence score 0.0 to 1.0
        """
        confidence = 0.0
        
        # Exact match = perfect confidence
        if marker.marker == definition.marker:
            confidence = 1.0
        
        # Normalize for comparison (remove spaces, colons)
        marker_norm = marker.marker.replace(' ', '').replace(':', '')
        def_norm = definition.marker.replace(' ', '').replace(':', '')
        
        if marker_norm == def_norm:
            confidence = 0.95
        
        # Same page = bonus
        if marker.page_number == definition.page_number:
            confidence += 0.3
        
        # Similar pattern type
        if self._same_marker_type(marker.marker, definition.marker):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _same_marker_type(self, marker1: str, marker2: str) -> bool:
        """Check if two markers are the same type (both asterisk, both ※, etc.)"""
        # Asterisk type
        if marker1.startswith('*') and marker2.startswith('*'):
            return True
        
        # Kome type
        if marker1.startswith('※') and marker2.startswith('※'):
            return True
        
        # Chu type
        if marker1.startswith('注') and marker2.startswith('注'):
            return True
        
        # Dagger
        if marker1 == '†' and marker2 == '†':
            return True
        if marker1 == '‡' and marker2 == '‡':
            return True
        
        # Bracketed
        if marker1.startswith('[') and marker2.startswith('['):
            return True
        
        # Parenthesized
        if marker1.startswith('(') and marker2.startswith('('):
            return True
        
        return False
    
    def verify_completeness(self, 
                          markers: List[FootnoteMarker],
                          definitions: List[FootnoteDefinition],
                          matches: List[FootnoteMatch]) -> Dict[str, any]:
        """
        Verify that all markers have definitions.
        
        Returns:
            Verification report
        """
        total_markers = len(markers)
        total_definitions = len(definitions)
        total_matches = len(matches)
        
        # Find unmatched
        matched_marker_texts = {m.marker.marker for m in matches}
        unmatched_markers = [m for m in markers if m.marker not in matched_marker_texts]
        
        matched_def_texts = {m.definition.marker for m in matches}
        unmatched_definitions = [d for d in definitions if d.marker not in matched_def_texts]
        
        # Calculate metrics
        if total_markers > 0:
            match_rate = (total_matches / total_markers) * 100
        else:
            match_rate = 100.0
        
        status = 'COMPLETE' if match_rate == 100 else 'PARTIAL' if match_rate >= 80 else 'POOR'
        
        report = {
            'total_markers': total_markers,
            'total_definitions': total_definitions,
            'total_matches': total_matches,
            'match_rate': round(match_rate, 1),
            'unmatched_markers': unmatched_markers,
            'unmatched_definitions': unmatched_definitions,
            'status': status
        }
        
        return report
    
    def print_report(self, report: Dict[str, any]):
        """Print human-readable verification report"""
        print("\n" + "="*60)
        print("FOOTNOTE VERIFICATION REPORT")
        print("="*60)
        
        status_icon = "✓" if report['status'] == 'COMPLETE' else "⚠" if report['status'] == 'PARTIAL' else "✗"
        
        print(f"\nStatus: {status_icon} {report['status']}")
        print(f"\nMarkers found:     {report['total_markers']}")
        print(f"Definitions found: {report['total_definitions']}")
        print(f"Matched pairs:     {report['total_matches']}")
        print(f"Match rate:        {report['match_rate']}%")
        
        if report['unmatched_markers']:
            print(f"\n⚠ Unmatched markers ({len(report['unmatched_markers'])}):")
            for marker in report['unmatched_markers'][:5]:  # Show first 5
                print(f"  - '{marker.marker}' on page {marker.page_number}")
            if len(report['unmatched_markers']) > 5:
                print(f"  ... and {len(report['unmatched_markers']) - 5} more")
        
        if report['unmatched_definitions']:
            print(f"\n⚠ Unmatched definitions ({len(report['unmatched_definitions'])}):")
            for defn in report['unmatched_definitions'][:5]:  # Show first 5
                preview = defn.text[:40] + "..." if len(defn.text) > 40 else defn.text
                print(f"  - '{defn.marker}': {preview}")
            if len(report['unmatched_definitions']) > 5:
                print(f"  ... and {len(report['unmatched_definitions']) - 5} more")
        
        print("\nInterpretation:")
        if report['status'] == 'COMPLETE':
            print("  ✓ All footnote markers have definitions")
            print("  ✓ Footnote system is complete")
        elif report['status'] == 'PARTIAL':
            print("  ⚠ Some markers are missing definitions")
            print("  ⚠ Review unmatched items above")
        else:
            print("  ✗ Many markers have no definitions")
            print("  ✗ Footnote extraction may have issues")
        
        print("="*60 + "\n")


# Convenience function
def analyze_footnotes(pdf_path: str) -> Dict[str, any]:
    """
    Quick function to analyze footnotes in a PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Analysis results with statistics
    """
    extractor = FootnoteExtractor()
    
    # Extract footnotes from all pages
    print(f"Analyzing footnotes in: {pdf_path}")
    all_footnotes = extractor.extract_footnotes_from_pdf(pdf_path)
    
    # Aggregate results
    all_markers = []
    all_definitions = []
    all_matches = []
    
    for page_num, (markers, definitions) in all_footnotes.items():
        all_markers.extend(markers)
        all_definitions.extend(definitions)
        
        # Match markers to definitions for this page
        matches = extractor.match_markers_to_definitions(markers, definitions)
        all_matches.extend(matches)
        
        if markers or definitions:
            print(f"  Page {page_num}: {len(markers)} markers, {len(definitions)} definitions, {len(matches)} matches")
    
    # Verify completeness
    report = extractor.verify_completeness(all_markers, all_definitions, all_matches)
    extractor.print_report(report)
    
    return {
        'markers': all_markers,
        'definitions': all_definitions,
        'matches': all_matches,
        'report': report
    }
