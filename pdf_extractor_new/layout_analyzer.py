"""
PHASE 2: LAYOUT INTELLIGENCE
Table detection, text box identification, and complex layout handling

This module:
1. Detects tables using line/border analysis
2. Extracts table structure with rows/columns
3. Identifies text boxes and sidebars
4. Preserves layout structure in output

Purpose: Handle complex document layouts without losing structure
"""
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class TableCell:
    """A single cell in a table"""
    text: str
    row: int
    col: int
    x0: float
    top: float
    x1: float
    bottom: float
    colspan: int = 1
    rowspan: int = 1
    
    def __repr__(self):
        return f"Cell({self.row},{self.col}): '{self.text[:20]}...'" if len(self.text) > 20 else f"Cell({self.row},{self.col}): '{self.text}'"


@dataclass
class Table:
    """A detected table with structure"""
    cells: List[TableCell]
    rows: int
    cols: int
    x0: float
    top: float
    x1: float
    bottom: float
    page_number: int
    confidence: float = 1.0
    has_header: bool = False
    
    def get_cell(self, row: int, col: int) -> Optional[TableCell]:
        """Get cell at specific position"""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None
    
    def to_text(self, style: str = "pipe") -> str:
        """Convert table to text format"""
        if style == "pipe":
            return self._to_pipe_format()
        elif style == "markdown":
            return self._to_markdown_format()
        elif style == "simple":
            return self._to_simple_format()
        else:
            return self._to_pipe_format()
    
    def _to_pipe_format(self) -> str:
        """Format as pipe-separated table"""
        # Build grid
        grid = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text.strip()
        
        # Calculate column widths
        col_widths = []
        for col in range(self.cols):
            max_width = 3  # Minimum width
            for row in range(self.rows):
                max_width = max(max_width, len(grid[row][col]))
            col_widths.append(min(max_width, 30))  # Cap at 30 chars
        
        # Build output
        lines = []
        for row_idx, row in enumerate(grid):
            cells = []
            for col_idx, cell_text in enumerate(row):
                # Truncate if too long
                if len(cell_text) > col_widths[col_idx]:
                    cell_text = cell_text[:col_widths[col_idx]-3] + "..."
                cells.append(cell_text.ljust(col_widths[col_idx]))
            lines.append(" | ".join(cells))
            
            # Add separator after header
            if row_idx == 0 and self.has_header:
                separator = "-+-".join("-" * w for w in col_widths)
                lines.append(separator)
        
        return "\n".join(lines)
    
    def _to_markdown_format(self) -> str:
        """Format as markdown table"""
        # Build grid
        grid = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text.strip()
        
        lines = []
        for row_idx, row in enumerate(grid):
            line = "| " + " | ".join(row) + " |"
            lines.append(line)
            
            # Add header separator after first row
            if row_idx == 0:
                separator = "|" + "|".join("---" for _ in range(self.cols)) + "|"
                lines.append(separator)
        
        return "\n".join(lines)
    
    def _to_simple_format(self) -> str:
        """Format as simple tab-separated"""
        grid = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text.strip()
        
        lines = []
        for row in grid:
            lines.append("\t".join(row))
        
        return "\n".join(lines)
    
    def __repr__(self):
        return f"Table({self.rows}x{self.cols} on page {self.page_number})"


@dataclass
class TextBox:
    """A detected text box or sidebar"""
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    page_number: int
    box_type: str = "generic"  # "sidebar", "callout", "note", "warning"
    has_border: bool = False
    has_background: bool = False
    
    def __repr__(self):
        preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"TextBox({self.box_type}): '{preview}'"


@dataclass
class LayoutRegion:
    """A region on the page with specific layout type"""
    region_type: str  # "table", "textbox", "figure", "text"
    x0: float
    top: float
    x1: float
    bottom: float
    content: Any  # Table, TextBox, or text string
    page_number: int


class LayoutAnalyzer:
    """
    Analyzes PDF page layouts to detect tables, text boxes, and complex structures.
    
    Uses multiple detection methods:
    1. Line/border analysis for tables
    2. pdfplumber's built-in table detection
    3. Spatial clustering for text boxes
    4. Visual element analysis
    """
    
    def __init__(self):
        # Table detection settings
        self.table_settings = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 10,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
        }
        
        # Alternative settings for tables without clear lines
        self.table_settings_text = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 5,
            "join_tolerance": 5,
        }
        
        # Text box detection thresholds
        self.textbox_min_words = 5
        self.textbox_isolation_threshold = 30  # pixels
        
        # Region detection
        self.min_table_rows = 2
        self.min_table_cols = 2
    
    def analyze_page(self, page, page_num: int) -> List[LayoutRegion]:
        """
        Analyze page layout and return detected regions.
        
        Args:
            page: pdfplumber page object
            page_num: Page number
            
        Returns:
            List of LayoutRegion objects
        """
        regions = []
        
        # Detect tables
        tables = self._detect_tables(page, page_num)
        for table in tables:
            region = LayoutRegion(
                region_type="table",
                x0=table.x0,
                top=table.top,
                x1=table.x1,
                bottom=table.bottom,
                content=table,
                page_number=page_num
            )
            regions.append(region)
        
        # Detect text boxes
        textboxes = self._detect_textboxes(page, page_num, tables)
        for textbox in textboxes:
            region = LayoutRegion(
                region_type="textbox",
                x0=textbox.x0,
                top=textbox.top,
                x1=textbox.x1,
                bottom=textbox.bottom,
                content=textbox,
                page_number=page_num
            )
            regions.append(region)
        
        # Sort regions by position (top to bottom, left to right)
        regions.sort(key=lambda r: (r.top, r.x0))
        
        return regions
    
    def _detect_tables(self, page, page_num: int) -> List[Table]:
        """
        Detect tables on a page.
        
        Uses multiple strategies:
        1. Line-based detection (clear borders)
        2. Text-based detection (no borders)
        """
        tables = []
        
        # Try line-based detection first
        try:
            line_tables = page.find_tables(self.table_settings)
            for pt in line_tables:
                table = self._convert_pdfplumber_table(pt, page_num, confidence=0.9)
                if table and table.rows >= self.min_table_rows and table.cols >= self.min_table_cols:
                    tables.append(table)
        except Exception as e:
            pass  # Line detection failed
        
        # If no tables found, try text-based detection
        if not tables:
            try:
                text_tables = page.find_tables(self.table_settings_text)
                for pt in text_tables:
                    table = self._convert_pdfplumber_table(pt, page_num, confidence=0.7)
                    if table and table.rows >= self.min_table_rows and table.cols >= self.min_table_cols:
                        tables.append(table)
            except Exception as e:
                pass  # Text detection also failed
        
        # Deduplicate overlapping tables
        tables = self._deduplicate_tables(tables)
        
        return tables
    
    def _convert_pdfplumber_table(self, pt, page_num: int, confidence: float = 0.9) -> Optional[Table]:
        """Convert pdfplumber table to our Table format"""
        try:
            # Extract table data
            data = pt.extract()
            if not data or len(data) < 2:
                return None
            
            # Get bounding box
            bbox = pt.bbox
            if not bbox:
                return None
            
            x0, top, x1, bottom = bbox
            
            # Create cells
            cells = []
            for row_idx, row in enumerate(data):
                if row is None:
                    continue
                for col_idx, cell_text in enumerate(row):
                    if cell_text is None:
                        cell_text = ""
                    
                    cell = TableCell(
                        text=str(cell_text).strip(),
                        row=row_idx,
                        col=col_idx,
                        x0=x0,  # Approximate
                        top=top,
                        x1=x1,
                        bottom=bottom
                    )
                    cells.append(cell)
            
            # Determine if first row is header
            has_header = self._detect_header_row(data)
            
            # Create table
            table = Table(
                cells=cells,
                rows=len(data),
                cols=max(len(row) for row in data if row) if data else 0,
                x0=x0,
                top=top,
                x1=x1,
                bottom=bottom,
                page_number=page_num,
                confidence=confidence,
                has_header=has_header
            )
            
            return table
            
        except Exception as e:
            return None
    
    def _detect_header_row(self, data: List[List[str]]) -> bool:
        """Detect if first row is a header"""
        if not data or len(data) < 2:
            return False
        
        first_row = data[0]
        if not first_row:
            return False
        
        # Check if first row has different characteristics
        # Headers often: all text, no numbers, shorter text
        
        first_row_text = [str(cell).strip() for cell in first_row if cell]
        other_rows_text = []
        for row in data[1:]:
            if row:
                other_rows_text.extend([str(cell).strip() for cell in row if cell])
        
        if not first_row_text or not other_rows_text:
            return False
        
        # Check if first row is all text (no pure numbers)
        first_row_all_text = all(not cell.replace('.', '').replace(',', '').isdigit() 
                                  for cell in first_row_text)
        
        # Check if other rows have numbers
        other_rows_have_numbers = any(cell.replace('.', '').replace(',', '').isdigit() 
                                      for cell in other_rows_text)
        
        return first_row_all_text and other_rows_have_numbers
    
    def _deduplicate_tables(self, tables: List[Table]) -> List[Table]:
        """Remove overlapping/duplicate tables"""
        if not tables:
            return []
        
        # Sort by confidence (higher first)
        tables.sort(key=lambda t: t.confidence, reverse=True)
        
        kept = []
        for table in tables:
            # Check if overlaps with any kept table
            overlaps = False
            for kept_table in kept:
                if self._tables_overlap(table, kept_table):
                    overlaps = True
                    break
            
            if not overlaps:
                kept.append(table)
        
        return kept
    
    def _tables_overlap(self, t1: Table, t2: Table) -> bool:
        """Check if two tables overlap"""
        # No overlap if one is completely to the left/right/above/below
        if t1.x1 < t2.x0 or t2.x1 < t1.x0:
            return False
        if t1.bottom < t2.top or t2.bottom < t1.top:
            return False
        return True
    
    def _detect_textboxes(self, page, page_num: int, tables: List[Table]) -> List[TextBox]:
        """
        Detect text boxes and sidebars.
        
        Looks for:
        - Bordered regions
        - Isolated text clusters
        - Shaded/highlighted regions
        """
        textboxes = []
        
        # Get all rectangles (potential text box borders)
        rects = page.rects if hasattr(page, 'rects') else []
        
        # Get all words
        words = page.extract_words()
        if not words:
            return []
        
        # For each rectangle, check if it contains text
        for rect in rects:
            # Skip very small rectangles
            width = rect.get('x1', 0) - rect.get('x0', 0)
            height = rect.get('bottom', 0) - rect.get('top', 0)
            
            if width < 50 or height < 20:
                continue
            
            # Skip if overlaps with a table
            rect_overlaps_table = False
            for table in tables:
                if self._rect_overlaps_table(rect, table):
                    rect_overlaps_table = True
                    break
            
            if rect_overlaps_table:
                continue
            
            # Find words inside this rectangle
            words_inside = []
            for word in words:
                if self._word_in_rect(word, rect):
                    words_inside.append(word)
            
            # If enough words, create a text box
            if len(words_inside) >= self.textbox_min_words:
                text = ' '.join(w['text'] for w in words_inside)
                
                # Determine box type
                box_type = self._classify_textbox(text, rect)
                
                textbox = TextBox(
                    text=text,
                    x0=rect.get('x0', 0),
                    top=rect.get('top', 0),
                    x1=rect.get('x1', 0),
                    bottom=rect.get('bottom', 0),
                    page_number=page_num,
                    box_type=box_type,
                    has_border=True
                )
                textboxes.append(textbox)
        
        # Also detect isolated text clusters (sidebars without borders)
        # This is done by finding text that's spatially separated from main content
        sidebars = self._detect_sidebars(words, page, page_num, tables, textboxes)
        textboxes.extend(sidebars)
        
        return textboxes
    
    def _rect_overlaps_table(self, rect: Dict, table: Table) -> bool:
        """Check if rectangle overlaps with table"""
        rx0, rtop = rect.get('x0', 0), rect.get('top', 0)
        rx1, rbottom = rect.get('x1', 0), rect.get('bottom', 0)
        
        if rx1 < table.x0 or table.x1 < rx0:
            return False
        if rbottom < table.top or table.bottom < rtop:
            return False
        return True
    
    def _word_in_rect(self, word: Dict, rect: Dict) -> bool:
        """Check if word is inside rectangle"""
        wx0, wtop = word.get('x0', 0), word.get('top', 0)
        wx1, wbottom = word.get('x1', 0), word.get('bottom', 0)
        
        rx0, rtop = rect.get('x0', 0), rect.get('top', 0)
        rx1, rbottom = rect.get('x1', 0), rect.get('bottom', 0)
        
        # Word center must be inside rect
        wcx = (wx0 + wx1) / 2
        wcy = (wtop + wbottom) / 2
        
        return rx0 <= wcx <= rx1 and rtop <= wcy <= rbottom
    
    def _classify_textbox(self, text: str, rect: Dict) -> str:
        """Classify text box type based on content"""
        text_lower = text.lower()
        
        # Warning/caution box
        if any(word in text_lower for word in ['warning', '警告', 'caution', '注意', 'danger', '危険']):
            return "warning"
        
        # Note/info box
        if any(word in text_lower for word in ['note', '注', 'info', '情報', 'tip', 'hint']):
            return "note"
        
        # Example box
        if any(word in text_lower for word in ['example', '例', 'sample', 'サンプル']):
            return "example"
        
        return "generic"
    
    def _detect_sidebars(self, words: List[Dict], page, page_num: int, 
                        tables: List[Table], existing_boxes: List[TextBox]) -> List[TextBox]:
        """Detect sidebar text that's spatially separated from main content"""
        if not words:
            return []
        
        sidebars = []
        page_width = page.width
        
        # Calculate main content boundaries
        x_positions = [w['x0'] for w in words]
        if not x_positions:
            return []
        
        # Find left and right margins
        left_margin = min(x_positions)
        right_margin = max(w['x1'] for w in words)
        content_width = right_margin - left_margin
        
        # Check for left sidebar (text in left 20% that's separated)
        left_threshold = left_margin + content_width * 0.2
        left_words = [w for w in words if w['x1'] < left_threshold]
        
        if left_words:
            # Check if there's a gap between left words and rest
            left_rightmost = max(w['x1'] for w in left_words)
            rest_words = [w for w in words if w['x0'] > left_rightmost]
            
            if rest_words:
                rest_leftmost = min(w['x0'] for w in rest_words)
                gap = rest_leftmost - left_rightmost
                
                if gap > self.textbox_isolation_threshold:
                    # This is a sidebar
                    text = ' '.join(w['text'] for w in sorted(left_words, key=lambda w: (w['top'], w['x0'])))
                    
                    if len(text.split()) >= self.textbox_min_words:
                        sidebar = TextBox(
                            text=text,
                            x0=min(w['x0'] for w in left_words),
                            top=min(w['top'] for w in left_words),
                            x1=max(w['x1'] for w in left_words),
                            bottom=max(w['bottom'] for w in left_words),
                            page_number=page_num,
                            box_type="sidebar",
                            has_border=False
                        )
                        sidebars.append(sidebar)
        
        # Similar check for right sidebar
        right_threshold = right_margin - content_width * 0.2
        right_words = [w for w in words if w['x0'] > right_threshold]
        
        if right_words:
            right_leftmost = min(w['x0'] for w in right_words)
            rest_words = [w for w in words if w['x1'] < right_leftmost]
            
            if rest_words:
                rest_rightmost = max(w['x1'] for w in rest_words)
                gap = right_leftmost - rest_rightmost
                
                if gap > self.textbox_isolation_threshold:
                    text = ' '.join(w['text'] for w in sorted(right_words, key=lambda w: (w['top'], w['x0'])))
                    
                    if len(text.split()) >= self.textbox_min_words:
                        sidebar = TextBox(
                            text=text,
                            x0=min(w['x0'] for w in right_words),
                            top=min(w['top'] for w in right_words),
                            x1=max(w['x1'] for w in right_words),
                            bottom=max(w['bottom'] for w in right_words),
                            page_number=page_num,
                            box_type="sidebar",
                            has_border=False
                        )
                        sidebars.append(sidebar)
        
        return sidebars
    
    def get_table_regions(self, page, page_num: int) -> List[Tuple[float, float, float, float]]:
        """Get bounding boxes of all tables on page"""
        tables = self._detect_tables(page, page_num)
        return [(t.x0, t.top, t.x1, t.bottom) for t in tables]
    
    def extract_tables_from_pdf(self, pdf_path: str) -> Dict[int, List[Table]]:
        """
        Extract all tables from a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page_number to list of tables
        """
        results = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = self._detect_tables(page, page_num)
                if tables:
                    results[page_num] = tables
        
        return results
    
    def format_table_output(self, table: Table, include_markers: bool = True) -> str:
        """
        Format table for text output.
        
        Args:
            table: Table to format
            include_markers: Include [TABLE] markers
            
        Returns:
            Formatted table text
        """
        parts = []
        
        if include_markers:
            parts.append(f"\n[TABLE: {table.rows}x{table.cols}]")
        
        parts.append(table.to_text(style="pipe"))
        
        if include_markers:
            parts.append("[TABLE END]\n")
        
        return "\n".join(parts)
    
    def format_textbox_output(self, textbox: TextBox, include_markers: bool = True) -> str:
        """
        Format text box for output.
        
        Args:
            textbox: TextBox to format
            include_markers: Include markers
            
        Returns:
            Formatted text box
        """
        parts = []
        
        if include_markers:
            box_label = textbox.box_type.upper()
            parts.append(f"\n[{box_label} BOX]")
        
        parts.append(textbox.text)
        
        if include_markers:
            parts.append(f"[{textbox.box_type.upper()} BOX END]\n")
        
        return "\n".join(parts)
    
    def print_layout_summary(self, regions: List[LayoutRegion]):
        """Print summary of detected layout regions"""
        print("\n" + "="*60)
        print("LAYOUT ANALYSIS SUMMARY")
        print("="*60)
        
        tables = [r for r in regions if r.region_type == "table"]
        textboxes = [r for r in regions if r.region_type == "textbox"]
        
        print(f"\nTotal regions: {len(regions)}")
        print(f"Tables: {len(tables)}")
        print(f"Text boxes: {len(textboxes)}")
        
        if tables:
            print("\nTables found:")
            for i, region in enumerate(tables, 1):
                table = region.content
                print(f"  {i}. {table.rows}x{table.cols} table on page {table.page_number}")
        
        if textboxes:
            print("\nText boxes found:")
            for i, region in enumerate(textboxes, 1):
                textbox = region.content
                preview = textbox.text[:40] + "..." if len(textbox.text) > 40 else textbox.text
                print(f"  {i}. [{textbox.box_type}] '{preview}' on page {textbox.page_number}")
        
        print("="*60 + "\n")


# Convenience functions
def analyze_pdf_layout(pdf_path: str) -> Dict[int, List[LayoutRegion]]:
    """
    Quick function to analyze layout of entire PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Dictionary mapping page_number to list of LayoutRegion
    """
    analyzer = LayoutAnalyzer()
    results = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            regions = analyzer.analyze_page(page, page_num)
            if regions:
                results[page_num] = regions
                print(f"Page {page_num}: {len(regions)} layout regions found")
    
    return results


def extract_all_tables(pdf_path: str) -> List[Table]:
    """
    Extract all tables from PDF.
    
    Args:
        pdf_path: Path to PDF
        
    Returns:
        List of all tables
    """
    analyzer = LayoutAnalyzer()
    all_tables = []
    
    tables_by_page = analyzer.extract_tables_from_pdf(pdf_path)
    for page_num, tables in tables_by_page.items():
        all_tables.extend(tables)
    
    return all_tables
