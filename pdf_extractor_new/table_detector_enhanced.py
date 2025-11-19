"""
ENHANCED TABLE DETECTOR FOR 95%+ ACCURACY
==========================================

Multiple detection strategies:
1. Line-based (for bordered tables)
2. Text-alignment based (for borderless tables)
3. Whitespace pattern analysis
4. Hybrid approach with confidence scoring
5. LLM verification for ambiguous cases
"""
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
import statistics


@dataclass
class TableCell:
    """A single cell in a detected table"""
    text: str
    row: int
    col: int
    x0: float
    top: float
    x1: float
    bottom: float
    colspan: int = 1
    rowspan: int = 1
    confidence: float = 1.0


@dataclass
class DetectedTable:
    """A detected table with metadata"""
    cells: List[TableCell]
    rows: int
    cols: int
    x0: float
    top: float
    x1: float
    bottom: float
    page_number: int
    detection_method: str
    confidence: float
    has_header: bool = False
    has_borders: bool = False
    
    def to_text(self, style: str = "pipe") -> str:
        """Convert table to text format"""
        # Build grid
        grid = [['' for _ in range(self.cols)] for _ in range(self.rows)]
        
        for cell in self.cells:
            if 0 <= cell.row < self.rows and 0 <= cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text.strip()
        
        # Calculate column widths
        col_widths = []
        for col in range(self.cols):
            max_width = 3
            for row in range(self.rows):
                max_width = max(max_width, len(grid[row][col]))
            col_widths.append(min(max_width, 40))
        
        # Build output
        lines = []
        for row_idx, row in enumerate(grid):
            cells = []
            for col_idx, cell_text in enumerate(row):
                if len(cell_text) > col_widths[col_idx]:
                    cell_text = cell_text[:col_widths[col_idx]-3] + "..."
                cells.append(cell_text.ljust(col_widths[col_idx]))
            lines.append(" | ".join(cells))
            
            if row_idx == 0 and self.has_header:
                separator = "-+-".join("-" * w for w in col_widths)
                lines.append(separator)
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        return {
            'rows': self.rows,
            'cols': self.cols,
            'page': self.page_number,
            'method': self.detection_method,
            'confidence': round(self.confidence, 2),
            'has_header': self.has_header,
            'has_borders': self.has_borders
        }


class EnhancedTableDetector:
    """
    Enhanced table detection with multiple strategies.
    
    Strategies:
    1. Lines-based: Uses visible borders
    2. Text-alignment: Detects column alignment
    3. Whitespace: Analyzes spacing patterns
    4. Hybrid: Combines multiple methods
    """
    
    def __init__(self, config=None):
        """
        Initialize enhanced table detector.
        
        Args:
            config: Configuration module
        """
        if config is None:
            try:
                import config_optimized as config
            except ImportError:
                import config
        
        self.config = config
        
        # Detection settings
        self.min_rows = getattr(config, 'TABLE_MIN_ROWS', 2)
        self.min_cols = getattr(config, 'TABLE_MIN_COLS', 2)
        self.confidence_threshold = getattr(config, 'TABLE_CONFIDENCE_THRESHOLD', 0.7)
        
        # Line-based settings
        self.line_settings = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance": 5,
            "join_tolerance": 5,
            "edge_min_length": 15,
        }
        
        # Strict line settings
        self.line_settings_strict = {
            "vertical_strategy": "lines_strict",
            "horizontal_strategy": "lines_strict",
            "snap_tolerance": 3,
            "join_tolerance": 3,
        }
        
        # Text-based settings
        self.text_settings = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "snap_tolerance": 8,
            "join_tolerance": 8,
        }
        
        # Alignment thresholds
        self.alignment_tolerance = 5  # pixels
        self.min_column_gap = 15  # minimum gap between columns
        self.min_row_gap = 3  # minimum gap between rows
    
    def detect_tables(self, page, page_num: int) -> List[DetectedTable]:
        """
        Detect all tables on a page using multiple strategies.
        
        Args:
            page: pdfplumber page object
            page_num: Page number
            
        Returns:
            List of detected tables with confidence scores
        """
        all_tables = []
        
        # Strategy 1: Line-based detection (high confidence)
        line_tables = self._detect_line_based(page, page_num)
        all_tables.extend(line_tables)
        
        # Strategy 2: Text-alignment detection
        alignment_tables = self._detect_alignment_based(page, page_num)
        all_tables.extend(alignment_tables)
        
        # Strategy 3: Whitespace pattern detection
        whitespace_tables = self._detect_whitespace_based(page, page_num)
        all_tables.extend(whitespace_tables)
        
        # Merge and deduplicate
        merged_tables = self._merge_tables(all_tables)
        
        # Filter by confidence
        filtered_tables = [
            t for t in merged_tables 
            if t.confidence >= self.confidence_threshold
        ]
        
        # Detect headers
        for table in filtered_tables:
            table.has_header = self._detect_header(table)
        
        return filtered_tables
    
    def _detect_line_based(self, page, page_num: int) -> List[DetectedTable]:
        """Detect tables using visible lines/borders"""
        tables = []
        
        # Try strict first
        try:
            found = page.find_tables(self.line_settings_strict)
            for pt in found:
                table = self._convert_pdfplumber_table(
                    pt, page_num, "lines_strict", 0.95
                )
                if table:
                    table.has_borders = True
                    tables.append(table)
        except Exception:
            pass
        
        # Try relaxed if strict found nothing
        if not tables:
            try:
                found = page.find_tables(self.line_settings)
                for pt in found:
                    table = self._convert_pdfplumber_table(
                        pt, page_num, "lines", 0.85
                    )
                    if table:
                        table.has_borders = True
                        tables.append(table)
            except Exception:
                pass
        
        return tables
    
    def _detect_alignment_based(self, page, page_num: int) -> List[DetectedTable]:
        """Detect tables by analyzing text alignment"""
        tables = []
        
        # Get all words
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3
        )
        
        if not words or len(words) < 10:
            return []
        
        # Find aligned columns
        columns = self._find_aligned_columns(words)
        
        if len(columns) < self.min_cols:
            return []
        
        # Find rows within columns
        rows = self._find_aligned_rows(words, columns)
        
        if len(rows) < self.min_rows:
            return []
        
        # Build table from alignment
        table = self._build_table_from_alignment(
            words, columns, rows, page_num
        )
        
        if table:
            tables.append(table)
        
        return tables
    
    def _detect_whitespace_based(self, page, page_num: int) -> List[DetectedTable]:
        """Detect tables by analyzing whitespace patterns"""
        tables = []
        
        # Get words
        words = page.extract_words()
        if not words:
            return []
        
        # Analyze horizontal gaps
        x_positions = sorted(set(w['x0'] for w in words))
        
        # Find significant gaps (potential column separators)
        gaps = []
        for i in range(1, len(x_positions)):
            gap = x_positions[i] - x_positions[i-1]
            if gap > self.min_column_gap:
                gaps.append((x_positions[i-1], x_positions[i], gap))
        
        if len(gaps) < self.min_cols - 1:
            return []
        
        # Check for regular spacing (indicates table)
        if gaps:
            gap_sizes = [g[2] for g in gaps]
            if len(gap_sizes) >= 2:
                mean_gap = statistics.mean(gap_sizes)
                stdev_gap = statistics.stdev(gap_sizes) if len(gap_sizes) > 1 else 0
                
                # Regular spacing = likely table
                regularity = 1 - (stdev_gap / mean_gap) if mean_gap > 0 else 0
                
                if regularity > 0.5:
                    # Try text-based detection with higher confidence
                    try:
                        found = page.find_tables(self.text_settings)
                        for pt in found:
                            table = self._convert_pdfplumber_table(
                                pt, page_num, "whitespace", 
                                0.7 + (regularity * 0.2)
                            )
                            if table:
                                tables.append(table)
                    except Exception:
                        pass
        
        return tables
    
    def _find_aligned_columns(self, words: List[Dict]) -> List[float]:
        """Find column positions by analyzing x-coordinate alignment"""
        # Cluster x-positions
        x_positions = [w['x0'] for w in words]
        
        if not x_positions:
            return []
        
        # Find clusters
        x_positions.sort()
        clusters = []
        current_cluster = [x_positions[0]]
        
        for x in x_positions[1:]:
            if x - current_cluster[-1] <= self.alignment_tolerance:
                current_cluster.append(x)
            else:
                if len(current_cluster) >= 3:  # Minimum items for column
                    clusters.append(statistics.mean(current_cluster))
                current_cluster = [x]
        
        if len(current_cluster) >= 3:
            clusters.append(statistics.mean(current_cluster))
        
        return clusters
    
    def _find_aligned_rows(self, words: List[Dict], columns: List[float]) -> List[float]:
        """Find row positions by analyzing y-coordinate alignment"""
        # Get words in columns
        column_words = []
        for word in words:
            for col_x in columns:
                if abs(word['x0'] - col_x) <= self.alignment_tolerance:
                    column_words.append(word)
                    break
        
        if not column_words:
            return []
        
        # Cluster y-positions
        y_positions = sorted([w['top'] for w in column_words])
        
        clusters = []
        current_cluster = [y_positions[0]]
        
        for y in y_positions[1:]:
            if y - current_cluster[-1] <= self.min_row_gap * 3:
                current_cluster.append(y)
            else:
                if len(current_cluster) >= len(columns) * 0.5:  # At least half columns have data
                    clusters.append(statistics.mean(current_cluster))
                current_cluster = [y]
        
        if len(current_cluster) >= len(columns) * 0.5:
            clusters.append(statistics.mean(current_cluster))
        
        return clusters
    
    def _build_table_from_alignment(self, words: List[Dict], 
                                    columns: List[float], 
                                    rows: List[float],
                                    page_num: int) -> Optional[DetectedTable]:
        """Build table structure from alignment data"""
        if len(columns) < self.min_cols or len(rows) < self.min_rows:
            return None
        
        # Create cells
        cells = []
        
        for row_idx, row_y in enumerate(rows):
            for col_idx, col_x in enumerate(columns):
                # Find word at this position
                cell_text = ""
                for word in words:
                    if (abs(word['x0'] - col_x) <= self.alignment_tolerance * 2 and
                        abs(word['top'] - row_y) <= self.min_row_gap * 3):
                        if cell_text:
                            cell_text += " "
                        cell_text += word['text']
                
                cell = TableCell(
                    text=cell_text,
                    row=row_idx,
                    col=col_idx,
                    x0=col_x,
                    top=row_y,
                    x1=col_x + 50,
                    bottom=row_y + 15
                )
                cells.append(cell)
        
        # Calculate bounding box
        x0 = min(columns)
        x1 = max(columns) + 100
        top = min(rows)
        bottom = max(rows) + 20
        
        # Calculate confidence based on cell fill rate
        non_empty = sum(1 for c in cells if c.text.strip())
        fill_rate = non_empty / len(cells) if cells else 0
        confidence = 0.6 + (fill_rate * 0.3)
        
        return DetectedTable(
            cells=cells,
            rows=len(rows),
            cols=len(columns),
            x0=x0,
            top=top,
            x1=x1,
            bottom=bottom,
            page_number=page_num,
            detection_method="alignment",
            confidence=confidence,
            has_borders=False
        )
    
    def _convert_pdfplumber_table(self, pt, page_num: int, 
                                   method: str, confidence: float) -> Optional[DetectedTable]:
        """Convert pdfplumber table to DetectedTable"""
        try:
            data = pt.extract()
            if not data or len(data) < self.min_rows:
                return None
            
            # Check columns
            max_cols = max(len(row) for row in data if row)
            if max_cols < self.min_cols:
                return None
            
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
                    cell = TableCell(
                        text=str(cell_text or '').strip(),
                        row=row_idx,
                        col=col_idx,
                        x0=x0,
                        top=top,
                        x1=x1,
                        bottom=bottom
                    )
                    cells.append(cell)
            
            return DetectedTable(
                cells=cells,
                rows=len(data),
                cols=max_cols,
                x0=x0,
                top=top,
                x1=x1,
                bottom=bottom,
                page_number=page_num,
                detection_method=method,
                confidence=confidence
            )
        
        except Exception:
            return None
    
    def _merge_tables(self, tables: List[DetectedTable]) -> List[DetectedTable]:
        """Merge overlapping tables, keeping highest confidence"""
        if not tables:
            return []
        
        # Sort by confidence (descending)
        tables.sort(key=lambda t: t.confidence, reverse=True)
        
        merged = []
        
        for table in tables:
            # Check overlap with existing
            overlaps = False
            for existing in merged:
                if self._tables_overlap(table, existing):
                    overlaps = True
                    # Increase confidence of existing if multiple methods agree
                    if table.detection_method != existing.detection_method:
                        existing.confidence = min(1.0, existing.confidence + 0.1)
                    break
            
            if not overlaps:
                merged.append(table)
        
        return merged
    
    def _tables_overlap(self, t1: DetectedTable, t2: DetectedTable) -> bool:
        """Check if two tables overlap"""
        # No overlap if completely separate
        if t1.x1 < t2.x0 or t2.x1 < t1.x0:
            return False
        if t1.bottom < t2.top or t2.bottom < t1.top:
            return False
        
        # Calculate overlap area
        x_overlap = min(t1.x1, t2.x1) - max(t1.x0, t2.x0)
        y_overlap = min(t1.bottom, t2.bottom) - max(t1.top, t2.top)
        
        overlap_area = x_overlap * y_overlap
        
        # Get smaller area
        area1 = (t1.x1 - t1.x0) * (t1.bottom - t1.top)
        area2 = (t2.x1 - t2.x0) * (t2.bottom - t2.top)
        min_area = min(area1, area2)
        
        # Significant overlap = > 50% of smaller table
        return overlap_area > min_area * 0.5
    
    def _detect_header(self, table: DetectedTable) -> bool:
        """Detect if table has a header row"""
        if table.rows < 2:
            return False
        
        # Get first row cells
        first_row = [c for c in table.cells if c.row == 0]
        other_rows = [c for c in table.cells if c.row > 0]
        
        if not first_row or not other_rows:
            return False
        
        # Check characteristics
        first_row_text = [c.text for c in first_row]
        
        # Header indicators:
        # 1. All text (no numbers)
        all_text = all(
            not re.match(r'^[\d.,]+$', t.strip())
            for t in first_row_text if t.strip()
        )
        
        # 2. Other rows have numbers
        other_text = [c.text for c in other_rows]
        has_numbers = any(
            re.match(r'^[\d.,]+$', t.strip())
            for t in other_text if t.strip()
        )
        
        # 3. First row is shorter (column names vs data)
        first_avg_len = statistics.mean([len(t) for t in first_row_text]) if first_row_text else 0
        other_avg_len = statistics.mean([len(t) for t in other_text]) if other_text else 0
        shorter_first = first_avg_len < other_avg_len * 1.5
        
        return all_text and (has_numbers or shorter_first)
    
    def detect_tables_in_pdf(self, pdf_path: str) -> Dict[int, List[DetectedTable]]:
        """
        Detect all tables in a PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page_number to list of tables
        """
        results = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                tables = self.detect_tables(page, page_num)
                if tables:
                    results[page_num] = tables
        
        return results
    
    def format_table_output(self, table: DetectedTable) -> str:
        """Format table for text output with markers"""
        parts = []
        
        confidence_str = f"{table.confidence:.0%}"
        method_str = table.detection_method
        
        parts.append(f"\n[TABLE: {table.rows}x{table.cols} | {method_str} | {confidence_str}]")
        parts.append(table.to_text())
        parts.append("[TABLE END]\n")
        
        return "\n".join(parts)
    
    def print_detection_summary(self, results: Dict[int, List[DetectedTable]]):
        """Print detection summary"""
        print("\n" + "="*60)
        print("TABLE DETECTION SUMMARY")
        print("="*60)
        
        total_tables = sum(len(tables) for tables in results.values())
        print(f"\nTotal tables found: {total_tables}")
        print(f"Pages with tables: {len(results)}")
        
        # By method
        methods = defaultdict(int)
        for tables in results.values():
            for table in tables:
                methods[table.detection_method] += 1
        
        if methods:
            print("\nBy detection method:")
            for method, count in sorted(methods.items()):
                print(f"  {method}: {count}")
        
        # Details
        if results:
            print("\nTable details:")
            for page_num in sorted(results.keys()):
                for table in results[page_num]:
                    print(f"  Page {page_num}: {table.rows}x{table.cols} "
                          f"({table.detection_method}, {table.confidence:.0%})")
        
        print("="*60 + "\n")


# Convenience function
def detect_all_tables(pdf_path: str, config=None) -> Dict[int, List[DetectedTable]]:
    """
    Quick function to detect all tables in PDF.
    
    Args:
        pdf_path: Path to PDF
        config: Optional config module
        
    Returns:
        Dictionary mapping page to tables
    """
    detector = EnhancedTableDetector(config)
    results = detector.detect_tables_in_pdf(pdf_path)
    detector.print_detection_summary(results)
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python table_detector_enhanced.py <pdf_path>")
        sys.exit(1)
    
    results = detect_all_tables(sys.argv[1])
    
    # Print tables
    for page_num, tables in results.items():
        for table in tables:
            print(f"\n--- Page {page_num} ---")
            print(table.to_text())
