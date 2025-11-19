"""
FLAGGING SYSTEM FOR REVIEW
Mark uncertain content and generate review reports

Features:
- Flag low-confidence sections
- Mark potential issues
- Generate review queue
- Track resolution status
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class FlagSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FlagType(Enum):
    LOW_CONFIDENCE = "low_confidence"
    OCR_ERROR = "ocr_error"
    MISSING_CONTENT = "missing_content"
    TABLE_ISSUE = "table_issue"
    FOOTNOTE_MISMATCH = "footnote_mismatch"
    ENCODING_ERROR = "encoding_error"
    LAYOUT_ISSUE = "layout_issue"
    CONSENSUS_CONFLICT = "consensus_conflict"
    MANUAL_REVIEW = "manual_review"


@dataclass
class Flag:
    """A single flag for review"""
    flag_id: str
    flag_type: FlagType
    severity: FlagSeverity
    page: int
    message: str
    context: str = ""
    suggested_fix: str = ""
    resolved: bool = False
    resolution_note: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'id': self.flag_id,
            'type': self.flag_type.value,
            'severity': self.severity.value,
            'page': self.page,
            'message': self.message,
            'context': self.context[:200] if self.context else "",
            'suggested_fix': self.suggested_fix,
            'resolved': self.resolved
        }


class FlaggingSystem:
    """System for flagging content that needs review"""
    
    def __init__(self):
        self.flags: List[Flag] = []
        self._counter = 0
    
    def add_flag(self, flag_type: FlagType, severity: FlagSeverity, page: int,
                 message: str, context: str = "", suggested_fix: str = "") -> Flag:
        """Add a new flag"""
        self._counter += 1
        flag = Flag(
            flag_id=f"FLAG-{self._counter:04d}",
            flag_type=flag_type, severity=severity, page=page,
            message=message, context=context, suggested_fix=suggested_fix
        )
        self.flags.append(flag)
        return flag
    
    def flag_low_confidence(self, page: int, text: str, confidence: float):
        """Flag low confidence extraction"""
        severity = FlagSeverity.HIGH if confidence < 0.5 else FlagSeverity.MEDIUM if confidence < 0.7 else FlagSeverity.LOW
        return self.add_flag(FlagType.LOW_CONFIDENCE, severity, page,
                           f"Low confidence ({confidence:.0%})", text, "Manual review recommended")
    
    def flag_ocr_error(self, page: int, text: str, pattern: str):
        """Flag potential OCR error"""
        return self.add_flag(FlagType.OCR_ERROR, FlagSeverity.MEDIUM, page,
                           f"OCR error: {pattern}", text, "Verify against original")
    
    def flag_missing_footnote(self, page: int, marker: str):
        """Flag missing footnote"""
        return self.add_flag(FlagType.FOOTNOTE_MISMATCH, FlagSeverity.MEDIUM, page,
                           f"Marker '{marker}' without definition", "", "Check page bottom")
    
    def flag_table_issue(self, page: int, issue: str):
        """Flag table issue"""
        return self.add_flag(FlagType.TABLE_ISSUE, FlagSeverity.MEDIUM, page,
                           f"Table: {issue}", "", "Verify structure")
    
    def resolve_flag(self, flag_id: str, note: str = "") -> bool:
        """Mark flag as resolved"""
        for flag in self.flags:
            if flag.flag_id == flag_id:
                flag.resolved = True
                flag.resolution_note = note
                return True
        return False
    
    def get_unresolved(self) -> List[Flag]:
        """Get unresolved flags"""
        return [f for f in self.flags if not f.resolved]
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        return {
            'total': len(self.flags),
            'unresolved': len(self.get_unresolved()),
            'critical': len([f for f in self.flags if f.severity == FlagSeverity.CRITICAL]),
            'high': len([f for f in self.flags if f.severity == FlagSeverity.HIGH]),
            'medium': len([f for f in self.flags if f.severity == FlagSeverity.MEDIUM]),
            'low': len([f for f in self.flags if f.severity == FlagSeverity.LOW])
        }
    
    def generate_report(self) -> str:
        """Generate review report"""
        summary = self.get_summary()
        lines = [
            "="*60, "REVIEW FLAGS REPORT", "="*60,
            f"\nTotal: {summary['total']}, Unresolved: {summary['unresolved']}",
            f"Critical: {summary['critical']}, High: {summary['high']}, Medium: {summary['medium']}, Low: {summary['low']}"
        ]
        
        unresolved = self.get_unresolved()
        if unresolved:
            lines.extend(["\n" + "="*60, "UNRESOLVED FLAGS", "="*60])
            for flag in unresolved:
                lines.append(f"\n{flag.flag_id} - Page {flag.page} [{flag.severity.value}]")
                lines.append(f"  {flag.message}")
                if flag.suggested_fix:
                    lines.append(f"  Fix: {flag.suggested_fix}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Export to JSON"""
        return json.dumps({
            'summary': self.get_summary(),
            'flags': [f.to_dict() for f in self.flags]
        }, indent=2, ensure_ascii=False)
    
    def save_report(self, filepath: str):
        """Save report to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_report())


if __name__ == "__main__":
    # Demo
    flagger = FlaggingSystem()
    flagger.flag_low_confidence(1, "Sample text...", 0.65)
    flagger.flag_ocr_error(3, "pat1ent", "1→i")
    flagger.flag_missing_footnote(5, "*1")
    print(flagger.generate_report())
