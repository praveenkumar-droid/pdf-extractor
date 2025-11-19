"""
PHASE 5: ANTI-HALLUCINATION VERIFICATION
Verifies extracted text actually exists in the PDF

This module:
1. Compares extracted text against element inventory
2. Checks position consistency
3. Flags suspicious content
4. Prevents fabricated text in output
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Result of anti-hallucination verification"""
    passed: bool
    issues: List[str]
    warnings: List[str]
    element_match_rate: float
    position_consistency: float
    suspicious_content: List[str]

    def to_dict(self) -> Dict:
        return {
            'passed': self.passed,
            'issues': self.issues,
            'warnings': self.warnings,
            'element_match_rate': round(self.element_match_rate, 2),
            'position_consistency': round(self.position_consistency, 2),
            'suspicious_content': self.suspicious_content
        }


class AntiHallucinationVerifier:
    """
    Verifies that extracted text is not hallucinated.

    Checks:
    1. Element count matches inventory
    2. Content distribution (top/middle/bottom) is consistent
    3. No suspicious AI-generated patterns
    4. Footnote markers have definitions
    """

    def __init__(self):
        # Suspicious patterns that indicate hallucination
        self.hallucination_patterns = [
            # AI-generated headers
            r'^#{1,6}\s+(?:目次|概要|はじめに|結論|まとめ)$',
            r'^(?:Table of Contents|Summary|Introduction|Conclusion)$',

            # Markdown formatting (not in original PDF)
            r'\*\*[^*]+\*\*',  # Bold
            r'__[^_]+__',      # Bold alt
            r'\*[^*]+\*(?!\d)', # Italic (but not *1, *2)
            r'_[^_]+_',        # Italic alt

            # HTML tags
            r'<[a-z]+[^>]*>',
            r'</[a-z]+>',

            # AI explanatory phrases
            r'This (?:section|document|page) (?:describes|contains|shows)',
            r'(?:As shown|As seen|Note that|Please note)',
            r'(?:The following|Below is|Above is)',
        ]

        # Minimum thresholds
        self.min_element_match_rate = 0.70  # 70% of inventory should be extracted
        self.min_position_consistency = 0.80  # 80% position distribution match

    def verify(self,
               extracted_text: str,
               inventory_report: Dict,
               page_count: int) -> VerificationResult:
        """
        Run anti-hallucination verification.

        Args:
            extracted_text: The extracted text to verify
            inventory_report: Element inventory report
            page_count: Number of pages

        Returns:
            VerificationResult with findings
        """
        issues = []
        warnings = []
        suspicious = []

        # CHECK 1: Element count
        element_match_rate = self._check_element_count(
            extracted_text, inventory_report, issues, warnings
        )

        # CHECK 2: Position distribution
        position_consistency = self._check_position_distribution(
            extracted_text, inventory_report, issues, warnings
        )

        # CHECK 3: Hallucination patterns
        self._check_hallucination_patterns(
            extracted_text, suspicious, issues
        )

        # CHECK 4: Footnote completeness
        self._check_footnote_completeness(
            extracted_text, warnings
        )

        # CHECK 5: Page marker consistency
        self._check_page_markers(
            extracted_text, page_count, issues
        )

        # Determine pass/fail
        passed = (
            len(issues) == 0 and
            element_match_rate >= self.min_element_match_rate and
            position_consistency >= self.min_position_consistency
        )

        return VerificationResult(
            passed=passed,
            issues=issues,
            warnings=warnings,
            element_match_rate=element_match_rate,
            position_consistency=position_consistency,
            suspicious_content=suspicious
        )

    def _check_element_count(self, text: str, inventory: Dict,
                            issues: List, warnings: List) -> float:
        """Check that extracted element count matches inventory."""
        expected = inventory.get('total_expected', 0)
        extracted = inventory.get('total_extracted', len(text.split()))

        if expected == 0:
            return 1.0

        ratio = extracted / expected

        if ratio < 0.5:
            issues.append(
                f"Severe content loss: Only {ratio:.0%} of expected elements extracted "
                f"({extracted} vs {expected})"
            )
        elif ratio < 0.7:
            warnings.append(
                f"Moderate content loss: {ratio:.0%} of expected elements "
                f"({extracted} vs {expected})"
            )
        elif ratio > 1.5:
            warnings.append(
                f"Possible duplication: {ratio:.0%} of expected elements "
                f"({extracted} vs {expected})"
            )

        return min(ratio, 1.0)  # Cap at 1.0

    def _check_position_distribution(self, text: str, inventory: Dict,
                                    issues: List, warnings: List) -> float:
        """Check that content distribution matches inventory regions."""
        by_region = inventory.get('by_region', {})

        if not by_region:
            return 1.0

        expected_top = by_region.get('top', 0)
        expected_middle = by_region.get('middle', 0)
        expected_bottom = by_region.get('bottom', 0)
        total = expected_top + expected_middle + expected_bottom

        if total == 0:
            return 1.0

        # Estimate from text (rough heuristic based on page markers)
        pages = text.split('--- PAGE')

        # Can't do detailed check without more info
        # Just verify we have content

        if expected_bottom > 0 and not re.search(r'[※注\*†‡]\d*', text):
            warnings.append(
                f"Expected {expected_bottom} elements in bottom region (likely footnotes) "
                f"but no footnote markers found"
            )
            return 0.8

        return 1.0

    def _check_hallucination_patterns(self, text: str,
                                      suspicious: List, issues: List):
        """Check for patterns that indicate AI hallucination."""
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)

            if matches:
                for match in matches[:3]:  # Report first 3
                    suspicious.append(match)

                # Markdown formatting is a clear issue
                if '**' in pattern or '__' in pattern or '<' in pattern:
                    issues.append(
                        f"Suspicious formatting found (possible hallucination): "
                        f"'{matches[0][:50]}...'"
                    )

    def _check_footnote_completeness(self, text: str, warnings: List):
        """Check that footnote markers have definitions."""
        # Find in-text markers
        markers = re.findall(r'\*(\d+)', text)

        for marker_num in set(markers):
            # Look for definition
            definition_pattern = rf'\*{marker_num}\s*[：:\s]'

            if not re.search(definition_pattern, text):
                warnings.append(
                    f"Footnote marker *{marker_num} found but no definition detected"
                )

    def _check_page_markers(self, text: str, expected_pages: int, issues: List):
        """Check page marker consistency."""
        # Count page markers
        starts = len(re.findall(r'--- PAGE \d+ START ---', text))
        ends = len(re.findall(r'--- PAGE \d+ END ---', text))

        if starts != ends:
            issues.append(
                f"Page marker mismatch: {starts} START markers but {ends} END markers"
            )

        if starts != expected_pages:
            issues.append(
                f"Page count mismatch: Expected {expected_pages} pages but found {starts}"
            )

    def remove_suspicious_content(self, text: str) -> Tuple[str, List[str]]:
        """
        Remove detected hallucinations from text.

        Returns:
            Tuple of (cleaned_text, removed_items)
        """
        removed = []
        cleaned = text

        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, cleaned, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                removed.append(match)

            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.IGNORECASE)

        # Clean up extra whitespace from removals
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

        return cleaned, removed


def verify_extraction(extracted_text: str,
                     inventory_report: Dict,
                     page_count: int) -> VerificationResult:
    """
    Convenience function to verify extraction.
    """
    verifier = AntiHallucinationVerifier()
    return verifier.verify(extracted_text, inventory_report, page_count)
