"""
PHASE 9: PAGE MARKERS AND OUTPUT FORMATTING
Professional output formatting with clear page boundaries

This module adds:
1. Document filename header
2. Page START/END markers
3. Quality markers for issues ([illegible], [uncertain], etc.)
4. Clean, professional formatting

Purpose: Make output readable, navigable, and professional
"""
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re


class OutputFormatter:
    """
    Formats extracted text with page markers and quality indicators.
    
    Adds:
    - Document filename header
    - Page boundary markers
    - Quality markers for issues
    - Metadata comments
    """
    
    def __init__(self):
        # Formatting settings
        self.page_marker_style = "dash"  # "dash", "equals", "hash"
        self.marker_length = 60
        self.add_timestamp = False
        self.add_statistics = False
        
        # Quality marker definitions
        self.quality_markers = {
            'illegible': '[illegible]',
            'uncertain': '[?]',
            'order_uncertain': '[order uncertain]',
            'possibly_superscript': '[possibly superscript]',
            'possibly_subscript': '[possibly subscript]',
            'empty_cell': '[empty]',
            'corrected': '[corrected]',
            'missing': '[missing text]',
        }
    
    def format_document(self, 
                       pages: List[str],
                       filename: str,
                       metadata: Optional[Dict] = None) -> str:
        """
        Format extracted pages with markers and metadata.
        
        Args:
            pages: List of page texts (one string per page)
            filename: Source PDF filename
            metadata: Optional metadata dict with stats
            
        Returns:
            Formatted text with page markers
        """
        output_parts = []
        
        # Add document header
        output_parts.append(self._create_header(filename, metadata))
        output_parts.append("")  # Blank line
        
        # Add each page with markers
        for page_num, page_text in enumerate(pages, 1):
            output_parts.append(self._create_page_marker(page_num, "START"))
            output_parts.append("")  # Blank line
            output_parts.append(page_text.strip())
            output_parts.append("")  # Blank line
            output_parts.append(self._create_page_marker(page_num, "END"))
            output_parts.append("")  # Blank line between pages
        
        # Add document footer (if statistics enabled)
        if self.add_statistics and metadata:
            output_parts.append(self._create_footer(metadata))
        
        # Join all parts
        formatted_text = "\n".join(output_parts)
        
        # Clean up excessive blank lines (max 2 consecutive)
        formatted_text = re.sub(r'\n{4,}', '\n\n\n', formatted_text)
        
        return formatted_text.strip()
    
    def _create_header(self, filename: str, metadata: Optional[Dict] = None) -> str:
        """Create document header with filename"""
        header_parts = []
        
        # Filename
        header_parts.append(f"[DOCUMENT FILENAME: {filename}]")
        
        # Optional timestamp
        if self.add_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header_parts.append(f"[EXTRACTED: {timestamp}]")
        
        # Optional metadata
        if metadata:
            if 'page_count' in metadata:
                header_parts.append(f"[PAGES: {metadata['page_count']}]")
            if 'word_count' in metadata:
                header_parts.append(f"[WORDS: {metadata['word_count']:,}]")
            if 'extraction_method' in metadata:
                header_parts.append(f"[METHOD: {metadata['extraction_method']}]")
        
        return "\n".join(header_parts)
    
    def _create_page_marker(self, page_num: int, marker_type: str) -> str:
        """
        Create page boundary marker.
        
        Args:
            page_num: Page number
            marker_type: "START" or "END"
        """
        if self.page_marker_style == "dash":
            marker_char = "-"
        elif self.page_marker_style == "equals":
            marker_char = "="
        elif self.page_marker_style == "hash":
            marker_char = "#"
        else:
            marker_char = "-"
        
        # Create marker line
        marker_text = f" PAGE {page_num} {marker_type} "
        padding = (self.marker_length - len(marker_text)) // 2
        
        if padding > 0:
            left_pad = marker_char * padding
            right_pad = marker_char * (self.marker_length - len(marker_text) - padding)
            marker_line = f"{left_pad}{marker_text}{right_pad}"
        else:
            marker_line = marker_text
        
        return marker_line
    
    def _create_footer(self, metadata: Dict) -> str:
        """Create document footer with statistics"""
        footer_parts = []
        footer_parts.append("")
        footer_parts.append("="*self.marker_length)
        footer_parts.append("EXTRACTION STATISTICS")
        footer_parts.append("="*self.marker_length)
        
        if 'page_count' in metadata:
            footer_parts.append(f"Total Pages: {metadata['page_count']}")
        if 'word_count' in metadata:
            footer_parts.append(f"Total Words: {metadata['word_count']:,}")
        if 'char_count' in metadata:
            footer_parts.append(f"Total Characters: {metadata['char_count']:,}")
        if 'extraction_time' in metadata:
            footer_parts.append(f"Extraction Time: {metadata['extraction_time']:.2f}s")
        
        footer_parts.append("="*self.marker_length)
        
        return "\n".join(footer_parts)
    
    def add_quality_marker(self, text: str, marker_type: str, position: Optional[int] = None) -> str:
        """
        Add a quality marker to text.
        
        Args:
            text: The text to mark
            marker_type: Type of marker (illegible, uncertain, etc.)
            position: Optional position to insert marker
            
        Returns:
            Text with quality marker added
        """
        if marker_type not in self.quality_markers:
            return text
        
        marker = self.quality_markers[marker_type]
        
        if position is not None:
            # Insert at specific position
            return text[:position] + marker + text[position:]
        else:
            # Append to end
            return text + " " + marker
    
    def format_table(self, rows: List[List[str]], title: Optional[str] = None) -> str:
        """
        Format a table with clear structure.
        
        Args:
            rows: List of rows, each row is list of cell values
            title: Optional table title
            
        Returns:
            Formatted table text
        """
        if not rows:
            return ""
        
        parts = []
        
        # Add title if provided
        if title:
            parts.append(f"\n[TABLE: {title}]")
        
        # Format rows
        for i, row in enumerate(rows):
            # Join cells with | separator
            row_text = " | ".join(str(cell) for cell in row)
            parts.append(row_text)
            
            # Add separator after header row
            if i == 0:
                parts.append("-" * len(row_text))
        
        parts.append("[TABLE END]\n")
        
        return "\n".join(parts)
    
    def format_footnotes(self, footnotes: List[Dict]) -> str:
        """
        Format footnotes section.
        
        Args:
            footnotes: List of footnote dicts with 'marker' and 'text'
            
        Returns:
            Formatted footnotes text
        """
        if not footnotes:
            return ""
        
        parts = []
        parts.append("\n" + "="*40)
        parts.append("FOOTNOTES:")
        parts.append("="*40)
        
        for fn in footnotes:
            marker = fn.get('marker', '')
            text = fn.get('text', '')
            parts.append(f"{marker}: {text}")
        
        return "\n".join(parts)
    
    def format_warning_box(self, content: str, box_type: str = "WARNING") -> str:
        """
        Format a warning or info box.
        
        Args:
            content: Box content
            box_type: Type (WARNING, CAUTION, NOTE, INFO)
            
        Returns:
            Formatted box text
        """
        width = self.marker_length
        
        parts = []
        parts.append("\n" + "!"*width)
        parts.append(f" {box_type} ".center(width, "!"))
        parts.append("!"*width)
        
        # Wrap content to width
        words = content.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width - 4:  # -4 for margins
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        for line in lines:
            parts.append(f"! {line.ljust(width-4)} !")
        
        parts.append("!"*width + "\n")
        
        return "\n".join(parts)
    
    def create_summary(self, pages: List[str], filename: str) -> Dict[str, any]:
        """
        Create extraction summary/metadata.
        
        Args:
            pages: List of page texts
            filename: Source filename
            
        Returns:
            Metadata dictionary
        """
        # Calculate statistics
        total_text = "\n\n".join(pages)
        
        metadata = {
            'filename': filename,
            'page_count': len(pages),
            'word_count': len(total_text.split()),
            'char_count': len(total_text),
            'extraction_method': 'pdfplumber',
            'timestamp': datetime.now().isoformat(),
        }
        
        # Per-page stats
        page_stats = []
        for i, page in enumerate(pages, 1):
            stats = {
                'page_number': i,
                'word_count': len(page.split()),
                'char_count': len(page),
                'has_content': bool(page.strip())
            }
            page_stats.append(stats)
        
        metadata['page_stats'] = page_stats
        
        return metadata
    
    def split_by_pages(self, text: str) -> List[str]:
        """
        Split formatted text back into pages.
        
        Args:
            text: Formatted text with page markers
            
        Returns:
            List of page texts
        """
        # Find all page boundaries
        page_pattern = r'--- PAGE (\d+) START ---\s*(.*?)\s*--- PAGE \1 END ---'
        matches = re.finditer(page_pattern, text, re.DOTALL)
        
        pages = []
        for match in matches:
            page_num = int(match.group(1))
            page_text = match.group(2).strip()
            pages.append(page_text)
        
        return pages
    
    def remove_markers(self, text: str) -> str:
        """
        Remove all formatting markers from text.
        
        Args:
            text: Formatted text with markers
            
        Returns:
            Clean text without markers
        """
        # Remove document header
        text = re.sub(r'\[DOCUMENT FILENAME:.*?\]', '', text)
        text = re.sub(r'\[EXTRACTED:.*?\]', '', text)
        text = re.sub(r'\[PAGES:.*?\]', '', text)
        text = re.sub(r'\[WORDS:.*?\]', '', text)
        
        # Remove page markers
        text = re.sub(r'[-=#+]+ PAGE \d+ (START|END) [-=#+]+', '', text)
        
        # Remove quality markers
        for marker in self.quality_markers.values():
            text = text.replace(marker, '')
        
        # Remove table markers
        text = re.sub(r'\[TABLE:.*?\]', '', text)
        text = re.sub(r'\[TABLE END\]', '', text)
        
        # Remove footnote markers
        text = re.sub(r'={40,}\nFOOTNOTES:\n={40,}', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


# Convenience function
def format_extracted_text(pages: List[str], 
                         pdf_path: str,
                         add_stats: bool = False) -> str:
    """
    Quick function to format extracted pages.
    
    Args:
        pages: List of page texts
        pdf_path: Path to source PDF
        add_stats: Whether to add statistics footer
        
    Returns:
        Formatted text with page markers
    """
    formatter = OutputFormatter()
    formatter.add_statistics = add_stats
    
    filename = Path(pdf_path).name
    metadata = formatter.create_summary(pages, filename)
    
    formatted = formatter.format_document(pages, filename, metadata)
    
    return formatted


# Example usage function
def demonstrate_formatting():
    """Demonstrate various formatting features"""
    formatter = OutputFormatter()
    
    # Example pages
    pages = [
        "This is page 1 content.\nMore text here.",
        "This is page 2 content.\nWith multiple lines.",
        "This is page 3 content.\nFinal page."
    ]
    
    # Format with markers
    result = formatter.format_document(pages, "example.pdf")
    print(result)
    
    print("\n" + "="*60)
    print("FORMATTING EXAMPLES")
    print("="*60)
    
    # Quality marker example
    text = "Some unclear text"
    marked = formatter.add_quality_marker(text, 'uncertain')
    print(f"\nQuality marker: {marked}")
    
    # Table example
    table = [
        ["Header 1", "Header 2", "Header 3"],
        ["Data 1", "Data 2", "Data 3"],
        ["Data 4", "Data 5", "Data 6"]
    ]
    table_text = formatter.format_table(table, "Example Table")
    print(f"\n{table_text}")
    
    # Warning box example
    warning = formatter.format_warning_box(
        "This is an important warning message that needs attention.",
        "WARNING"
    )
    print(warning)


if __name__ == "__main__":
    demonstrate_formatting()
