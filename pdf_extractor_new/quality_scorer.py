"""
PHASE 7: QUALITY SCORING SYSTEM
Evaluates and scores extraction quality for reliability assessment

This module:
1. Scores extractions on multiple dimensions
2. Provides overall quality grade (A-F)
3. Identifies specific issues
4. Recommends actions for low-quality extractions

Purpose: Know which extractions are reliable vs need manual review
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class QualityGrade(Enum):
    """Quality grade levels"""
    A = "Excellent"      # 90-100%
    B = "Good"           # 80-89%
    C = "Acceptable"     # 70-79%
    D = "Poor"           # 60-69%
    F = "Failed"         # <60%


@dataclass
class QualityDimension:
    """Score for a single quality dimension"""
    name: str
    score: float          # 0-100
    weight: float         # Importance weight
    issues: List[str]     # Specific issues found
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class QualityReport:
    """Complete quality assessment report"""
    overall_score: float
    grade: QualityGrade
    dimensions: List[QualityDimension]
    issues: List[str]
    recommendations: List[str]
    confidence: float
    
    def to_dict(self) -> Dict:
        return {
            'overall_score': round(self.overall_score, 1),
            'grade': self.grade.value,
            'confidence': round(self.confidence, 2),
            'dimensions': {
                d.name: {
                    'score': round(d.score, 1),
                    'weight': d.weight,
                    'issues': d.issues
                }
                for d in self.dimensions
            },
            'issues': self.issues,
            'recommendations': self.recommendations
        }


class QualityScorer:
    """
    Scores extraction quality on multiple dimensions.
    
    Dimensions:
    1. Completeness - How much content was captured
    2. Structure - Tables, sections, formatting preserved
    3. Accuracy - Character preservation, no corruption
    4. Footnotes - Markers matched with definitions
    5. Readability - Output is clean and usable
    """
    
    def __init__(self):
        # Dimension weights (must sum to 1.0)
        self.weights = {
            'completeness': 0.30,
            'structure': 0.25,
            'accuracy': 0.20,
            'footnotes': 0.15,
            'readability': 0.10
        }
        
        # Thresholds
        self.grade_thresholds = {
            QualityGrade.A: 90,
            QualityGrade.B: 80,
            QualityGrade.C: 70,
            QualityGrade.D: 60,
            QualityGrade.F: 0
        }
    
    def score_extraction(self,
                        extracted_text: str,
                        inventory_report: Optional[Dict] = None,
                        footnote_report: Optional[Dict] = None,
                        table_count: int = 0,
                        page_count: int = 1) -> QualityReport:
        """
        Score an extraction on all quality dimensions.
        
        Args:
            extracted_text: The extracted text
            inventory_report: Element inventory verification report
            footnote_report: Footnote matching report
            table_count: Number of tables detected
            page_count: Number of pages
            
        Returns:
            QualityReport with scores and recommendations
        """
        dimensions = []
        all_issues = []
        
        # Score each dimension
        completeness = self._score_completeness(extracted_text, inventory_report, page_count)
        dimensions.append(completeness)
        all_issues.extend(completeness.issues)
        
        structure = self._score_structure(extracted_text, table_count, page_count)
        dimensions.append(structure)
        all_issues.extend(structure.issues)
        
        accuracy = self._score_accuracy(extracted_text)
        dimensions.append(accuracy)
        all_issues.extend(accuracy.issues)
        
        footnotes = self._score_footnotes(footnote_report)
        dimensions.append(footnotes)
        all_issues.extend(footnotes.issues)
        
        readability = self._score_readability(extracted_text)
        dimensions.append(readability)
        all_issues.extend(readability.issues)
        
        # Calculate overall score
        overall_score = sum(d.weighted_score for d in dimensions)
        
        # Determine grade
        grade = self._determine_grade(overall_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(dimensions)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dimensions, grade)
        
        return QualityReport(
            overall_score=overall_score,
            grade=grade,
            dimensions=dimensions,
            issues=all_issues,
            recommendations=recommendations,
            confidence=confidence
        )
    
    def _score_completeness(self, text: str, inventory_report: Optional[Dict], 
                           page_count: int) -> QualityDimension:
        """Score content completeness"""
        issues = []
        
        if inventory_report:
            coverage = inventory_report.get('coverage_percent', 0)
            score = min(coverage, 100)
            
            if coverage < 70:
                issues.append(f"Low coverage: {coverage:.1f}% of elements extracted")
            elif coverage < 85:
                issues.append(f"Moderate coverage: {coverage:.1f}%")
        else:
            # Estimate from text
            words = len(text.split())
            expected_words = page_count * 300  # Rough estimate
            
            if words < expected_words * 0.5:
                score = 50
                issues.append(f"Very few words extracted ({words})")
            elif words < expected_words * 0.7:
                score = 70
                issues.append(f"Below expected word count")
            else:
                score = 90
        
        # Check for empty pages
        if "[extraction error]" in text.lower():
            score -= 10
            issues.append("Some pages had extraction errors")
        
        return QualityDimension(
            name="completeness",
            score=max(0, min(100, score)),
            weight=self.weights['completeness'],
            issues=issues
        )
    
    def _score_structure(self, text: str, table_count: int, 
                        page_count: int) -> QualityDimension:
        """Score structure preservation"""
        issues = []
        score = 100
        
        # Check for page markers
        if "PAGE" not in text and "page" not in text.lower():
            score -= 10
            issues.append("No page markers found")
        
        # Check for section numbers
        import re
        section_pattern = r'\d+\.\d+'
        sections = re.findall(section_pattern, text)
        if not sections and page_count > 3:
            score -= 10
            issues.append("No section numbers detected")
        
        # Check tables
        if table_count == 0 and page_count > 5:
            score -= 5
            issues.append("No tables detected (may be expected)")
        elif "[TABLE" in text:
            # Tables were formatted
            score += 5
        
        # Check for broken structure indicators
        if re.search(r'\n{5,}', text):
            score -= 5
            issues.append("Excessive blank lines detected")
        
        return QualityDimension(
            name="structure",
            score=max(0, min(100, score)),
            weight=self.weights['structure'],
            issues=issues
        )
    
    def _score_accuracy(self, text: str) -> QualityDimension:
        """Score character accuracy"""
        issues = []
        score = 100
        
        import re
        
        # Check for OCR-like errors
        ocr_patterns = [
            (r'[a-z][0-9][a-z]', "Possible OCR errors (digits in words)"),
            (r'\?\?\?+', "Unknown character sequences"),
            (r'□+', "Placeholder characters"),
        ]
        
        for pattern, issue_desc in ocr_patterns:
            matches = re.findall(pattern, text)
            if len(matches) > 5:
                score -= 10
                issues.append(f"{issue_desc}: {len(matches)} instances")
        
        # Check for encoding issues
        if '�' in text:
            count = text.count('�')
            score -= min(20, count)
            issues.append(f"Encoding errors: {count} replacement characters")
        
        # Check Japanese character integrity
        jp_chars = len(re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
        total_chars = len(text)
        
        if total_chars > 100 and jp_chars / total_chars < 0.3:
            # Expected Japanese but low ratio
            pass  # Might be English doc, don't penalize
        
        return QualityDimension(
            name="accuracy",
            score=max(0, min(100, score)),
            weight=self.weights['accuracy'],
            issues=issues
        )
    
    def _score_footnotes(self, footnote_report: Optional[Dict]) -> QualityDimension:
        """Score footnote handling"""
        issues = []
        
        if not footnote_report:
            # No footnote data available
            return QualityDimension(
                name="footnotes",
                score=80,  # Neutral score
                weight=self.weights['footnotes'],
                issues=["Footnote analysis not performed"]
            )
        
        match_rate = footnote_report.get('match_rate', 0)
        total_markers = footnote_report.get('total_markers', 0)
        
        if total_markers == 0:
            # No footnotes in document
            score = 100
        else:
            score = match_rate
            
            if match_rate < 80:
                unmatched = footnote_report.get('total_markers', 0) - footnote_report.get('total_matches', 0)
                issues.append(f"Low footnote match rate: {match_rate:.1f}%")
                issues.append(f"{unmatched} markers without definitions")
        
        return QualityDimension(
            name="footnotes",
            score=max(0, min(100, score)),
            weight=self.weights['footnotes'],
            issues=issues
        )
    
    def _score_readability(self, text: str) -> QualityDimension:
        """Score output readability"""
        issues = []
        score = 100
        
        import re
        
        # Check line length variance (should be reasonable)
        lines = [l for l in text.split('\n') if l.strip()]
        if lines:
            lengths = [len(l) for l in lines]
            avg_length = sum(lengths) / len(lengths)
            
            # Very short average suggests fragmented text
            if avg_length < 20:
                score -= 10
                issues.append("Very short average line length")
            
            # Very long lines suggest missing line breaks
            long_lines = sum(1 for l in lengths if l > 200)
            if long_lines > len(lines) * 0.1:
                score -= 5
                issues.append(f"{long_lines} very long lines detected")
        
        # Check for repeated content
        chunks = [text[i:i+100] for i in range(0, len(text)-100, 100)]
        unique_chunks = len(set(chunks))
        if chunks and unique_chunks / len(chunks) < 0.5:
            score -= 15
            issues.append("Possible repeated content detected")
        
        # Check for document markers
        if "[DOCUMENT FILENAME:" in text:
            score += 5  # Good formatting
        
        return QualityDimension(
            name="readability",
            score=max(0, min(100, score)),
            weight=self.weights['readability'],
            issues=issues
        )
    
    def _determine_grade(self, score: float) -> QualityGrade:
        """Determine letter grade from score"""
        for grade, threshold in self.grade_thresholds.items():
            if score >= threshold:
                return grade
        return QualityGrade.F
    
    def _calculate_confidence(self, dimensions: List[QualityDimension]) -> float:
        """Calculate confidence in the quality assessment"""
        # Lower confidence if dimensions have high variance
        scores = [d.score for d in dimensions]
        if not scores:
            return 0.5
        
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        
        # High variance = lower confidence
        confidence = 1.0 - min(0.5, variance / 1000)
        
        return max(0.3, min(1.0, confidence))
    
    def _generate_recommendations(self, dimensions: List[QualityDimension], 
                                  grade: QualityGrade) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Find lowest scoring dimensions
        sorted_dims = sorted(dimensions, key=lambda d: d.score)
        
        for dim in sorted_dims[:2]:  # Focus on two lowest
            if dim.score < 70:
                if dim.name == "completeness":
                    recommendations.append("Review filtering rules - content may be over-filtered")
                    recommendations.append("Check for scanned/image-based pages")
                elif dim.name == "structure":
                    recommendations.append("Verify table detection settings")
                    recommendations.append("Check page marker generation")
                elif dim.name == "accuracy":
                    recommendations.append("Enable LLM verification for OCR error correction")
                    recommendations.append("Check source PDF quality")
                elif dim.name == "footnotes":
                    recommendations.append("Review footnote region threshold")
                    recommendations.append("Check footnote marker patterns")
                elif dim.name == "readability":
                    recommendations.append("Review line joining rules")
                    recommendations.append("Check for duplicate content")
        
        # Grade-based recommendations
        if grade in [QualityGrade.D, QualityGrade.F]:
            recommendations.insert(0, "⚠️ Manual review strongly recommended")
        elif grade == QualityGrade.C:
            recommendations.insert(0, "Consider manual spot-check")
        
        return recommendations
    
    def print_report(self, report: QualityReport):
        """Print human-readable quality report"""
        print("\n" + "="*60)
        print("QUALITY ASSESSMENT REPORT")
        print("="*60)
        
        # Grade with color indicator
        grade_icons = {
            QualityGrade.A: "🟢",
            QualityGrade.B: "🟢",
            QualityGrade.C: "🟡",
            QualityGrade.D: "🟠",
            QualityGrade.F: "🔴"
        }
        
        icon = grade_icons.get(report.grade, "")
        print(f"\nOverall Grade: {icon} {report.grade.name} ({report.grade.value})")
        print(f"Overall Score: {report.overall_score:.1f}/100")
        print(f"Confidence: {report.confidence:.0%}")
        
        print("\nDimension Scores:")
        for dim in report.dimensions:
            bar = "█" * int(dim.score / 10) + "░" * (10 - int(dim.score / 10))
            print(f"  {dim.name:15} [{bar}] {dim.score:.0f}")
        
        if report.issues:
            print(f"\nIssues Found ({len(report.issues)}):")
            for issue in report.issues[:5]:  # Show top 5
                print(f"  • {issue}")
            if len(report.issues) > 5:
                print(f"  ... and {len(report.issues) - 5} more")
        
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations[:3]:  # Show top 3
                print(f"  → {rec}")
        
        print("="*60 + "\n")


# Convenience function
def score_extraction(text: str, **kwargs) -> QualityReport:
    """
    Quick function to score extraction quality.
    
    Args:
        text: Extracted text
        **kwargs: Additional data (inventory_report, footnote_report, etc.)
        
    Returns:
        QualityReport
    """
    scorer = QualityScorer()
    return scorer.score_extraction(text, **kwargs)


if __name__ == "__main__":
    # Demo
    sample_text = """
    [DOCUMENT FILENAME: test.pdf]
    
    --- PAGE 1 START ---
    
    1.1 Introduction
    This is sample content.
    
    --- PAGE 1 END ---
    """
    
    scorer = QualityScorer()
    report = scorer.score_extraction(
        sample_text,
        page_count=1,
        table_count=0
    )
    scorer.print_report(report)
