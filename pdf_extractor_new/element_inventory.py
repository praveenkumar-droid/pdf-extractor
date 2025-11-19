"""
PHASE 0: ELEMENT INVENTORY SYSTEM
Pre-extraction analysis to ensure completeness

This module counts and maps ALL text elements BEFORE extraction,
then verifies the extracted content matches the inventory.

Purpose: Prevent accidentally missing text during extraction
"""
import pdfplumber
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ElementInventory:
    """Complete inventory of text elements on a page"""
    page_number: int
    total_elements: int
    
    # By position
    top_region: int       # Elements in top 15% of page
    middle_region: int    # Elements in middle 70% of page
    bottom_region: int    # Elements in bottom 15% of page
    
    # By size (approximate categories)
    large_text: int       # Font size > 18pt (titles)
    standard_text: int    # Font size 10-18pt (body)
    small_text: int       # Font size 6-10pt (footnotes)
    tiny_text: int        # Font size < 6pt (super/subscripts)
    
    # Position map
    elements_by_position: List[Tuple[float, float, str]]  # (x, y, text)
    
    # Size distribution
    size_distribution: Dict[str, int]  # {size_range: count}
    
    def __repr__(self):
        return (f"PageInventory(page={self.page_number}, "
                f"total={self.total_elements}, "
                f"top={self.top_region}, "
                f"middle={self.middle_region}, "
                f"bottom={self.bottom_region})")


class ElementInventoryAnalyzer:
    """
    Analyzes PDF pages to create complete element inventory.
    
    This runs BEFORE extraction to count all elements, providing
    a baseline for verification after extraction.
    """
    
    def __init__(self):
        # Region boundaries (as percentage of page height)
        self.top_boundary = 0.15      # Top 15% is "top region"
        self.bottom_boundary = 0.85   # Bottom 15% is "bottom region"
        
        # Size categories (approximate - pdfplumber may not always provide size)
        self.large_threshold = 18     # > 18pt = large (titles)
        self.standard_min = 10        # 10-18pt = standard (body)
        self.small_min = 6            # 6-10pt = small (footnotes)
        # < 6pt = tiny (super/subscripts)
    
    def analyze_pdf(self, pdf_path: str) -> Dict[int, ElementInventory]:
        """
        Create complete inventory of all PDF pages.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary mapping page_number to ElementInventory
        """
        inventories = {}
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                inventory = self._analyze_page(page, page_num)
                inventories[page_num] = inventory
        
        return inventories
    
    def _analyze_page(self, page, page_num: int) -> ElementInventory:
        """
        Create inventory for a single page.
        
        Counts all text elements and categorizes by:
        - Position (top/middle/bottom)
        - Size (large/standard/small/tiny)
        """
        # Extract all words with detailed information
        words = page.extract_words(
            x_tolerance=3,
            y_tolerance=3,
            keep_blank_chars=False,
            extra_attrs=['size', 'fontname']  # Try to get font info
        )
        
        if not words:
            # Empty page
            return ElementInventory(
                page_number=page_num,
                total_elements=0,
                top_region=0,
                middle_region=0,
                bottom_region=0,
                large_text=0,
                standard_text=0,
                small_text=0,
                tiny_text=0,
                elements_by_position=[],
                size_distribution={}
            )
        
        # Get page dimensions
        page_height = page.height
        top_boundary_y = page_height * self.top_boundary
        bottom_boundary_y = page_height * self.bottom_boundary
        
        # Count by position
        top_count = 0
        middle_count = 0
        bottom_count = 0
        
        # Count by size
        large_count = 0
        standard_count = 0
        small_count = 0
        tiny_count = 0
        
        # Position map
        position_map = []
        
        # Size distribution
        size_dist = defaultdict(int)
        
        # Analyze each element
        for word in words:
            text = word.get('text', '')
            x = word.get('x0', 0)
            y = word.get('top', 0)
            
            # Position category
            if y < top_boundary_y:
                top_count += 1
            elif y > bottom_boundary_y:
                bottom_count += 1
            else:
                middle_count += 1
            
            # Add to position map (store as tuple for verification)
            position_map.append((x, y, text))
            
            # Size category (if available)
            size = word.get('size', None)
            if size is not None:
                if size > self.large_threshold:
                    large_count += 1
                    size_dist['large'] += 1
                elif size >= self.standard_min:
                    standard_count += 1
                    size_dist['standard'] += 1
                elif size >= self.small_min:
                    small_count += 1
                    size_dist['small'] += 1
                else:
                    tiny_count += 1
                    size_dist['tiny'] += 1
            else:
                # Size not available - estimate from height
                height = word.get('height', 10)
                if height > 18:
                    large_count += 1
                    size_dist['large (estimated)'] += 1
                elif height >= 10:
                    standard_count += 1
                    size_dist['standard (estimated)'] += 1
                elif height >= 6:
                    small_count += 1
                    size_dist['small (estimated)'] += 1
                else:
                    tiny_count += 1
                    size_dist['tiny (estimated)'] += 1
        
        # Create inventory
        inventory = ElementInventory(
            page_number=page_num,
            total_elements=len(words),
            top_region=top_count,
            middle_region=middle_count,
            bottom_region=bottom_count,
            large_text=large_count,
            standard_text=standard_count,
            small_text=small_count,
            tiny_text=tiny_count,
            elements_by_position=position_map,
            size_distribution=dict(size_dist)
        )
        
        return inventory
    
    def verify_extraction(self, 
                         inventories: Dict[int, ElementInventory],
                         extracted_text: str,
                         page_count: int) -> Dict[str, any]:
        """
        Verify extracted text against inventory.
        
        This is a rough verification - counts words in extracted text
        and compares to inventory counts.
        
        Args:
            inventories: Element inventories from analyze_pdf
            extracted_text: The extracted text
            page_count: Number of pages in PDF
            
        Returns:
            Verification report with statistics
        """
        # Count total elements expected
        total_expected = sum(inv.total_elements for inv in inventories.values())
        
        # Count words in extracted text (rough approximation)
        # Split by whitespace and newlines
        extracted_words = extracted_text.split()
        extracted_count = len(extracted_words)
        
        # Calculate coverage
        if total_expected > 0:
            coverage_percent = (extracted_count / total_expected) * 100
        else:
            coverage_percent = 0
        
        # Calculate missing
        missing = max(0, total_expected - extracted_count)
        missing_percent = (missing / total_expected * 100) if total_expected > 0 else 0
        
        # Check by region
        region_stats = {
            'top': sum(inv.top_region for inv in inventories.values()),
            'middle': sum(inv.middle_region for inv in inventories.values()),
            'bottom': sum(inv.bottom_region for inv in inventories.values())
        }
        
        # Check by size
        size_stats = {
            'large': sum(inv.large_text for inv in inventories.values()),
            'standard': sum(inv.standard_text for inv in inventories.values()),
            'small': sum(inv.small_text for inv in inventories.values()),
            'tiny': sum(inv.tiny_text for inv in inventories.values())
        }
        
        # Create report
        report = {
            'total_expected': total_expected,
            'total_extracted': extracted_count,
            'missing': missing,
            'coverage_percent': round(coverage_percent, 2),
            'missing_percent': round(missing_percent, 2),
            'pages_analyzed': page_count,
            'by_region': region_stats,
            'by_size': size_stats,
            'status': 'GOOD' if coverage_percent >= 85 else 
                     'WARNING' if coverage_percent >= 70 else 'POOR'
        }
        
        return report
    
    def print_inventory_summary(self, inventories: Dict[int, ElementInventory]):
        """Print human-readable summary of inventories"""
        print("\n" + "="*60)
        print("ELEMENT INVENTORY SUMMARY")
        print("="*60)
        
        total_elements = sum(inv.total_elements for inv in inventories.values())
        
        print(f"\nTotal Pages: {len(inventories)}")
        print(f"Total Elements: {total_elements:,}")
        
        # By position
        total_top = sum(inv.top_region for inv in inventories.values())
        total_middle = sum(inv.middle_region for inv in inventories.values())
        total_bottom = sum(inv.bottom_region for inv in inventories.values())
        
        print(f"\nBy Position:")
        print(f"  Top region (15%):     {total_top:,} ({total_top/total_elements*100:.1f}%)")
        print(f"  Middle region (70%):  {total_middle:,} ({total_middle/total_elements*100:.1f}%)")
        print(f"  Bottom region (15%):  {total_bottom:,} ({total_bottom/total_elements*100:.1f}%)")
        
        # By size
        total_large = sum(inv.large_text for inv in inventories.values())
        total_standard = sum(inv.standard_text for inv in inventories.values())
        total_small = sum(inv.small_text for inv in inventories.values())
        total_tiny = sum(inv.tiny_text for inv in inventories.values())
        
        print(f"\nBy Size:")
        print(f"  Large (>18pt):    {total_large:,} ({total_large/total_elements*100:.1f}%)")
        print(f"  Standard (10-18): {total_standard:,} ({total_standard/total_elements*100:.1f}%)")
        print(f"  Small (6-10):     {total_small:,} ({total_small/total_elements*100:.1f}%)")
        print(f"  Tiny (<6):        {total_tiny:,} ({total_tiny/total_elements*100:.1f}%)")
        
        # Per-page summary
        print(f"\nPer-Page Breakdown:")
        for page_num in sorted(inventories.keys())[:5]:  # Show first 5 pages
            inv = inventories[page_num]
            print(f"  Page {inv.page_number}: {inv.total_elements} elements "
                  f"(top:{inv.top_region}, mid:{inv.middle_region}, bot:{inv.bottom_region})")
        
        if len(inventories) > 5:
            print(f"  ... ({len(inventories) - 5} more pages)")
        
        print("="*60 + "\n")
    
    def print_verification_report(self, report: Dict[str, any]):
        """Print human-readable verification report"""
        print("\n" + "="*60)
        print("EXTRACTION VERIFICATION REPORT")
        print("="*60)
        
        status = report['status']
        status_icon = "✓" if status == "GOOD" else "⚠" if status == "WARNING" else "✗"
        
        print(f"\nStatus: {status_icon} {status}")
        print(f"\nTotal Expected:  {report['total_expected']:,} elements")
        print(f"Total Extracted: {report['total_extracted']:,} words")
        print(f"Coverage:        {report['coverage_percent']:.1f}%")
        print(f"Missing:         {report['missing']:,} ({report['missing_percent']:.1f}%)")
        
        print(f"\nBy Region:")
        for region, count in report['by_region'].items():
            print(f"  {region.capitalize():8} {count:,} elements")
        
        print(f"\nBy Size:")
        for size, count in report['by_size'].items():
            print(f"  {size.capitalize():10} {count:,} elements")
        
        # Interpretation
        print(f"\nInterpretation:")
        if status == "GOOD":
            print("  ✓ Extraction coverage is good (≥85%)")
            print("  ✓ Most content appears to be captured")
        elif status == "WARNING":
            print("  ⚠ Extraction coverage is moderate (70-85%)")
            print("  ⚠ Some content may be missing - review needed")
        else:
            print("  ✗ Extraction coverage is poor (<70%)")
            print("  ✗ Significant content missing - investigation required")
        
        print("\nNote: This is a rough verification based on word counts.")
        print("Manual review recommended for critical documents.")
        print("="*60 + "\n")


# Convenience function for quick analysis
def analyze_and_verify(pdf_path: str, extracted_text: str) -> Dict[str, any]:
    """
    Quick function to analyze PDF and verify extraction.
    
    Args:
        pdf_path: Path to PDF file
        extracted_text: The extracted text to verify
        
    Returns:
        Verification report
    """
    analyzer = ElementInventoryAnalyzer()
    
    # Create inventory
    print("Creating element inventory...")
    inventories = analyzer.analyze_pdf(pdf_path)
    analyzer.print_inventory_summary(inventories)
    
    # Verify extraction
    print("Verifying extraction...")
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
    
    report = analyzer.verify_extraction(inventories, extracted_text, page_count)
    analyzer.print_verification_report(report)
    
    return report
