"""
PHASE 5: LLM VERIFICATION SYSTEM
AI-powered verification and correction of extracted text

This module:
1. Identifies uncertain/problematic text regions
2. Sends to LLM for verification with context
3. Receives corrections and confidence scores
4. Applies fixes with transparency markers
5. Logs all changes for audit trail

Purpose: Use LLM intelligence to catch and fix errors that rule-based systems miss

IMPORTANT: This module provides the framework for LLM verification.
You need to configure your LLM API (OpenAI, Anthropic, local, etc.) to use it.
"""
import re
import json
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerificationIssue:
    """An identified issue that needs LLM verification"""
    issue_type: str
    original_text: str
    context_before: str
    context_after: str
    page_number: int
    position: int
    confidence: float
    
    def __repr__(self):
        preview = self.original_text[:30] + "..." if len(self.original_text) > 30 else self.original_text
        return f"Issue({self.issue_type}): '{preview}' [conf: {self.confidence:.2f}]"


@dataclass
class VerificationResult:
    """Result of LLM verification for an issue"""
    issue: VerificationIssue
    corrected_text: str
    llm_confidence: float
    explanation: str
    was_changed: bool
    timestamp: str
    
    def __repr__(self):
        status = "changed" if self.was_changed else "unchanged"
        return f"Result({status}): '{self.corrected_text[:30]}...' [conf: {self.llm_confidence:.2f}]"


@dataclass
class VerificationReport:
    """Complete report of all verifications performed"""
    total_issues_found: int
    total_corrections_made: int
    issues: List[VerificationIssue]
    results: List[VerificationResult]
    processing_time: float
    llm_calls_made: int
    average_confidence: float
    
    def to_dict(self) -> Dict:
        return {
            'total_issues_found': self.total_issues_found,
            'total_corrections_made': self.total_corrections_made,
            'processing_time': self.processing_time,
            'llm_calls_made': self.llm_calls_made,
            'average_confidence': self.average_confidence,
            'corrections': [
                {
                    'original': r.issue.original_text,
                    'corrected': r.corrected_text,
                    'type': r.issue.issue_type,
                    'confidence': r.llm_confidence,
                    'explanation': r.explanation
                }
                for r in self.results if r.was_changed
            ]
        }


class LLMVerifier:
    """
    LLM-powered text verification and correction system.
    
    Supported LLM backends:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Local models (via API)
    - Mock mode (for testing)
    """
    
    def __init__(self, 
                 llm_backend: str = "mock",
                 api_key: Optional[str] = None,
                 model: str = "gpt-4",
                 max_tokens: int = 1000,
                 temperature: float = 0.1):
        self.llm_backend = llm_backend
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Issue detection patterns
        self.ocr_error_patterns = [
            (r'[a-zA-Z]+[0-9]+[a-zA-Z]+', 'digit_in_word'),
            (r'[0-9]+[a-zA-Z]+[0-9]+', 'letter_in_number'),
            (r'\b[Il1][Il1]+\b', 'ambiguous_il1'),
            (r'\b[O0][O0]+\b', 'ambiguous_o0'),
            (r'[a-z][A-Z][a-z]', 'random_caps'),
            (r'rn(?=[a-z])', 'rn_as_m'),
        ]
        
        self.broken_word_patterns = [
            (r'\w+\s+(?:ing|ed|tion|ment|ness|ly)\b', 'broken_suffix'),
            (r'\b(?:un|re|pre|dis)\s+\w+', 'broken_prefix'),
            (r'\w+-\s*\n\s*\w+', 'hyphenated_break'),
        ]
        
        self.formatting_patterns = [
            (r'\s{3,}', 'excess_spaces'),
            (r'[。、]{2,}', 'duplicate_punct'),
            (r'\n{4,}', 'excess_newlines'),
        ]
        
        self.context_chars = 100
        self.min_issue_confidence = 0.6
        self.batch_size = 5
        
        self.stats = {
            'issues_found': 0,
            'llm_calls': 0,
            'corrections_made': 0,
            'total_time': 0
        }
    
    def verify_text(self, text: str, page_number: int = 1) -> Tuple[str, VerificationReport]:
        """Verify and correct text using LLM."""
        start_time = time.time()
        
        issues = self._identify_issues(text, page_number)
        
        if not issues:
            report = VerificationReport(
                total_issues_found=0,
                total_corrections_made=0,
                issues=[],
                results=[],
                processing_time=time.time() - start_time,
                llm_calls_made=0,
                average_confidence=1.0
            )
            return text, report
        
        logger.info(f"Found {len(issues)} potential issues to verify")
        
        results = []
        for i in range(0, len(issues), self.batch_size):
            batch = issues[i:i + self.batch_size]
            batch_results = self._verify_batch(batch)
            results.extend(batch_results)
        
        corrected_text = self._apply_corrections(text, results)
        
        corrections_made = sum(1 for r in results if r.was_changed)
        avg_confidence = (
            sum(r.llm_confidence for r in results) / len(results) 
            if results else 1.0
        )
        
        report = VerificationReport(
            total_issues_found=len(issues),
            total_corrections_made=corrections_made,
            issues=issues,
            results=results,
            processing_time=time.time() - start_time,
            llm_calls_made=self.stats['llm_calls'],
            average_confidence=avg_confidence
        )
        
        return corrected_text, report
    
    def _identify_issues(self, text: str, page_number: int) -> List[VerificationIssue]:
        """Identify potential issues in text"""
        issues = []
        
        for pattern, issue_type in self.ocr_error_patterns:
            for match in re.finditer(pattern, text):
                confidence = self._calculate_issue_confidence(match.group(), issue_type)
                if confidence >= self.min_issue_confidence:
                    issue = VerificationIssue(
                        issue_type=f"ocr_{issue_type}",
                        original_text=match.group(),
                        context_before=text[max(0, match.start() - self.context_chars):match.start()],
                        context_after=text[match.end():match.end() + self.context_chars],
                        page_number=page_number,
                        position=match.start(),
                        confidence=confidence
                    )
                    issues.append(issue)
        
        for pattern, issue_type in self.broken_word_patterns:
            for match in re.finditer(pattern, text):
                confidence = self._calculate_issue_confidence(match.group(), issue_type)
                if confidence >= self.min_issue_confidence:
                    issue = VerificationIssue(
                        issue_type=f"broken_{issue_type}",
                        original_text=match.group(),
                        context_before=text[max(0, match.start() - self.context_chars):match.start()],
                        context_after=text[match.end():match.end() + self.context_chars],
                        page_number=page_number,
                        position=match.start(),
                        confidence=confidence
                    )
                    issues.append(issue)
        
        for pattern, issue_type in self.formatting_patterns:
            for match in re.finditer(pattern, text):
                issue = VerificationIssue(
                    issue_type=f"format_{issue_type}",
                    original_text=match.group(),
                    context_before=text[max(0, match.start() - self.context_chars):match.start()],
                    context_after=text[match.end():match.end() + self.context_chars],
                    page_number=page_number,
                    position=match.start(),
                    confidence=0.8
                )
                issues.append(issue)
        
        issues.sort(key=lambda i: i.position)
        issues = self._remove_overlapping_issues(issues)
        
        return issues
    
    def _calculate_issue_confidence(self, text: str, issue_type: str) -> float:
        """Calculate confidence that this is actually an issue"""
        confidence = 0.7
        
        if issue_type == 'digit_in_word':
            if not re.match(r'^[A-Z]+\d+$', text):
                confidence = 0.85
            else:
                confidence = 0.3
        elif issue_type == 'ambiguous_il1':
            confidence = 0.75
        elif issue_type == 'broken_suffix':
            confidence = 0.9
        elif issue_type == 'broken_prefix':
            confidence = 0.85
        
        return confidence
    
    def _remove_overlapping_issues(self, issues: List[VerificationIssue]) -> List[VerificationIssue]:
        """Remove overlapping issues, keeping highest confidence"""
        if not issues:
            return []
        
        kept = [issues[0]]
        
        for issue in issues[1:]:
            prev = kept[-1]
            prev_end = prev.position + len(prev.original_text)
            
            if issue.position < prev_end:
                if issue.confidence > prev.confidence:
                    kept[-1] = issue
            else:
                kept.append(issue)
        
        return kept
    
    def _verify_batch(self, issues: List[VerificationIssue]) -> List[VerificationResult]:
        """Verify a batch of issues with LLM"""
        results = []
        for issue in issues:
            result = self._verify_single_issue(issue)
            results.append(result)
        return results
    
    def _verify_single_issue(self, issue: VerificationIssue) -> VerificationResult:
        """Verify a single issue with LLM"""
        prompt = self._build_verification_prompt(issue)
        llm_response = self._call_llm(prompt)
        corrected_text, confidence, explanation = self._parse_llm_response(
            llm_response, issue.original_text
        )
        
        result = VerificationResult(
            issue=issue,
            corrected_text=corrected_text,
            llm_confidence=confidence,
            explanation=explanation,
            was_changed=(corrected_text != issue.original_text),
            timestamp=datetime.now().isoformat()
        )
        
        return result
    
    def _build_verification_prompt(self, issue: VerificationIssue) -> str:
        """Build prompt for LLM verification"""
        return f"""You are a text verification assistant. Check if extracted text contains errors and correct them.

Issue Type: {issue.issue_type}
Original Text: "{issue.original_text}"
Context Before: "...{issue.context_before}"
Context After: "{issue.context_after}..."

Respond in JSON format:
{{"corrected_text": "your correction or original", "confidence": 0.95, "explanation": "brief explanation"}}

Only fix clear errors. If uncertain, keep the original."""
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API"""
        self.stats['llm_calls'] += 1
        
        if self.llm_backend == "mock":
            return self._mock_llm_response(prompt)
        elif self.llm_backend == "openai":
            return self._call_openai(prompt)
        elif self.llm_backend == "anthropic":
            return self._call_anthropic(prompt)
        elif self.llm_backend == "local":
            return self._call_local(prompt)
        else:
            logger.warning(f"Unknown LLM backend: {self.llm_backend}, using mock")
            return self._mock_llm_response(prompt)
    
    def _mock_llm_response(self, prompt: str) -> str:
        """Generate mock LLM response for testing"""
        match = re.search(r'Original Text: "([^"]*)"', prompt)
        original = match.group(1) if match else ""
        
        corrected = original
        explanation = "No issues found"
        confidence = 0.9
        
        # Safe patterns to NOT modify
        safe_patterns = [
            r'^[A-Z]+\d+$',      # MP3, CO2, H2O
            r'^\d+[A-Z]+$',      # 3D, 4K
            r'^[A-Z]\d+[A-Z]$',  # A4, B5
            r'\d+\.\d+',         # Version numbers
        ]
        
        is_safe = any(re.match(pattern, original) for pattern in safe_patterns)
        
        if is_safe:
            response = {
                "corrected_text": original,
                "confidence": 0.95,
                "explanation": "Known pattern - no correction needed"
            }
            return json.dumps(response)
        
        # Fix OCR errors
        if re.search(r'[a-z][0-9][a-z]', original):
            corrected = re.sub(r'(?<=[a-z])1(?=[a-z])', 'i', corrected)
            corrected = re.sub(r'(?<=[a-z])0(?=[a-z])', 'o', corrected)
            corrected = re.sub(r'(?<=[a-z])5(?=[a-z])', 's', corrected)
            if corrected != original:
                explanation = "Fixed OCR digit-letter confusion"
                confidence = 0.85
        
        # Fix broken suffix
        elif re.search(r'\w{3,}\s+(?:ing|ed|tion|ment|ness|ly|er|est|ous|ive|able|ible)\b', original):
            corrected = re.sub(r'(\w{3,})\s+(ing|ed|tion|ment|ness|ly|er|est|ous|ive|able|ible)\b', r'\1\2', original)
            if corrected != original:
                explanation = "Joined broken word suffix"
                confidence = 0.90
        
        # Fix broken prefix
        elif re.search(r'\b(un|re|pre|dis|mis|non|over|under)\s+\w{3,}', original):
            corrected = re.sub(r'\b(un|re|pre|dis|mis|non|over|under)\s+(\w{3,})', r'\1\2', original)
            if corrected != original:
                explanation = "Joined broken word prefix"
                confidence = 0.88
        
        # Fix excess spaces
        elif re.search(r'\s{3,}', original):
            corrected = re.sub(r'\s{3,}', '  ', original)
            if corrected != original:
                explanation = "Reduced excess whitespace"
                confidence = 0.95
        
        response = {
            "corrected_text": corrected,
            "confidence": confidence,
            "explanation": explanation
        }
        
        return json.dumps(response)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise text verification assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._mock_llm_response(prompt)
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._mock_llm_response(prompt)
    
    def _call_local(self, prompt: str) -> str:
        """Call local LLM API"""
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Local LLM API error: {e}")
            return self._mock_llm_response(prompt)
    
    def _parse_llm_response(self, response: str, original: str) -> Tuple[str, float, str]:
        """Parse LLM response JSON"""
        try:
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                corrected = data.get('corrected_text', original)
                confidence = float(data.get('confidence', 0.5))
                explanation = data.get('explanation', 'No explanation provided')
                return corrected, confidence, explanation
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        
        return original, 0.5, "Failed to parse LLM response"
    
    def _apply_corrections(self, text: str, results: List[VerificationResult]) -> str:
        """Apply corrections to text"""
        sorted_results = sorted(results, key=lambda r: r.issue.position, reverse=True)
        corrected_text = text
        
        for result in sorted_results:
            if result.was_changed and result.llm_confidence >= 0.7:
                start = result.issue.position
                end = start + len(result.issue.original_text)
                corrected_text = corrected_text[:start] + result.corrected_text + corrected_text[end:]
                self.stats['corrections_made'] += 1
                logger.info(f"Corrected: '{result.issue.original_text}' → '{result.corrected_text}'")
        
        return corrected_text
    
    def print_report(self, report: VerificationReport):
        """Print human-readable verification report"""
        print("\n" + "="*60)
        print("LLM VERIFICATION REPORT")
        print("="*60)
        print(f"\nIssues found:      {report.total_issues_found}")
        print(f"Corrections made:  {report.total_corrections_made}")
        print(f"LLM calls:         {report.llm_calls_made}")
        print(f"Processing time:   {report.processing_time:.2f}s")
        print(f"Avg confidence:    {report.average_confidence:.2f}")
        
        if report.results:
            print("\nCorrections made:")
            for result in report.results:
                if result.was_changed:
                    print(f"  • '{result.issue.original_text}' → '{result.corrected_text}'")
                    print(f"    Confidence: {result.llm_confidence:.2f}")
        
        print("="*60 + "\n")


def verify_extracted_text(text: str, llm_backend: str = "mock", 
                         api_key: Optional[str] = None) -> Tuple[str, VerificationReport]:
    """Quick function to verify extracted text."""
    verifier = LLMVerifier(llm_backend=llm_backend, api_key=api_key)
    return verifier.verify_text(text)


if __name__ == "__main__":
    sample_text = """
    The pat1ent rece1ved the medicat ion at 3pm.
    The concentrat ion of the so1ution was 5%.
    This    has   excess    spaces.
    """
    
    print("Original text:")
    print(sample_text)
    
    verifier = LLMVerifier(llm_backend="mock")
    corrected, report = verifier.verify_text(sample_text)
    
    print("\nCorrected text:")
    print(corrected)
    verifier.print_report(report)
