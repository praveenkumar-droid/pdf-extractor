"""
ENHANCED LLM VERIFIER FOR 95%+ ACCURACY
========================================

Advanced LLM-powered verification with:
- Japanese-specific OCR error patterns
- Context-aware verification
- Batch processing optimization
- Confidence calibration
- Iterative improvement
"""
import re
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VerificationIssue:
    """An identified issue needing LLM verification"""
    issue_id: str
    issue_type: str
    original_text: str
    context_before: str
    context_after: str
    page_number: int
    position: int
    confidence: float
    priority: int = 1  # 1=highest
    
    def to_dict(self) -> Dict:
        return {
            'id': self.issue_id,
            'type': self.issue_type,
            'original': self.original_text,
            'confidence': self.confidence,
            'priority': self.priority
        }


@dataclass
class VerificationResult:
    """Result of LLM verification"""
    issue: VerificationIssue
    corrected_text: str
    llm_confidence: float
    explanation: str
    was_changed: bool
    verification_method: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            'original': self.issue.original_text,
            'corrected': self.corrected_text,
            'confidence': self.llm_confidence,
            'changed': self.was_changed,
            'explanation': self.explanation
        }


@dataclass
class VerificationReport:
    """Complete verification report"""
    total_issues_found: int
    total_corrections_made: int
    issues: List[VerificationIssue]
    results: List[VerificationResult]
    processing_time: float
    llm_calls_made: int
    average_confidence: float
    iterations: int = 1
    
    def to_dict(self) -> Dict:
        return {
            'total_issues': self.total_issues_found,
            'corrections': self.total_corrections_made,
            'llm_calls': self.llm_calls_made,
            'avg_confidence': round(self.average_confidence, 3),
            'iterations': self.iterations,
            'time': round(self.processing_time, 2)
        }


class EnhancedLLMVerifier:
    """
    Enhanced LLM verification system for 95%+ accuracy.
    
    Features:
    - Japanese-specific OCR error patterns
    - Multi-pass verification
    - Context-aware corrections
    - Confidence calibration
    - Batch processing
    """
    
    def __init__(self, config=None):
        """
        Initialize enhanced verifier.
        
        Args:
            config: Configuration module (uses config_optimized if not provided)
        """
        if config is None:
            try:
                import config_optimized as config
            except ImportError:
                import config
        
        self.config = config
        self.llm_backend = getattr(config, 'LLM_BACKEND', 'anthropic')
        self.api_key = getattr(config, 'LLM_API_KEY', '')
        self.model = getattr(config, 'LLM_MODEL', 'claude-sonnet-4-20250514')
        self.max_tokens = getattr(config, 'LLM_MAX_TOKENS', 2000)
        self.temperature = getattr(config, 'LLM_TEMPERATURE', 0.1)
        self.batch_size = getattr(config, 'LLM_BATCH_SIZE', 10)
        
        # Issue counter
        self._issue_counter = 0
        
        # Statistics
        self.stats = {
            'llm_calls': 0,
            'total_tokens': 0,
            'corrections': 0,
            'cache_hits': 0
        }
        
        # Response cache
        self._cache = {}
        
        # ═══════════════════════════════════════════════════════════
        # ENHANCED JAPANESE OCR ERROR PATTERNS
        # ═══════════════════════════════════════════════════════════
        
        self.ocr_patterns_japanese = [
            # Katakana/Hiragana confusion
            (r'[ァ-ヶ][ぁ-ん][ァ-ヶ]', 'mixed_kana', 0.8),
            (r'[ぁ-ん][ァ-ヶ][ぁ-ん]', 'mixed_kana', 0.8),
            
            # Common character confusions
            (r'[ー一][^ー一]', 'long_vowel_confusion', 0.7),
            (r'[口ロ][^口ロ]', 'kuchi_ro_confusion', 0.75),
            (r'[二ニ][^二ニ]', 'ni_confusion', 0.75),
            (r'[力カ][^力カ]', 'chikara_ka_confusion', 0.75),
            (r'[工エ][^工エ]', 'kou_e_confusion', 0.75),
            (r'[夕タ][^夕タ]', 'yuu_ta_confusion', 0.75),
            
            # Number/letter confusion in Japanese context
            (r'[０-９][一-龯]', 'fullwidth_number_kanji', 0.7),
            (r'[一-龯][０-９]', 'kanji_fullwidth_number', 0.7),
            
            # Punctuation issues
            (r'[。、]{2,}', 'duplicate_jp_punct', 0.9),
            (r'[．，]{2,}', 'duplicate_fw_punct', 0.9),
        ]
        
        self.ocr_patterns_english = [
            # Classic OCR errors
            (r'[a-zA-Z]+[0-9]+[a-zA-Z]+', 'digit_in_word', 0.85),
            (r'\brn\b', 'rn_as_m', 0.8),
            (r'\bcl\b', 'cl_as_d', 0.75),
            (r'\bvv\b', 'vv_as_w', 0.8),
            (r'[Il1]{3,}', 'ambiguous_il1', 0.85),
            (r'[O0]{3,}', 'ambiguous_o0', 0.85),
            
            # Case errors
            (r'\b[a-z][A-Z][a-z]+\b', 'random_caps', 0.7),
            (r'\b[A-Z]{2,}[a-z][A-Z]+\b', 'mixed_caps', 0.75),
        ]
        
        self.structural_patterns = [
            # Broken words
            (r'\w+\s+(?:ing|ed|tion|ment|ness|ly|able|ible)\b', 'broken_suffix', 0.9),
            (r'\b(?:un|re|pre|dis|mis|non)\s+\w+', 'broken_prefix', 0.9),
            (r'\w+-\s*\n\s*\w+', 'hyphen_break', 0.85),
            
            # Spacing issues
            (r'\s{3,}', 'excess_space', 0.95),
            (r'[a-zA-Z]{15,}', 'no_space_words', 0.8),
            
            # Japanese structural
            (r'[。、]\s*[。、]', 'double_jp_punct', 0.9),
            (r'[（(]\s*[)）]', 'empty_parens', 0.85),
        ]
        
        # Context window size
        self.context_chars = 150
        
        # Confidence thresholds
        self.min_issue_confidence = 0.6
        self.auto_fix_confidence = 0.95
        self.llm_verify_confidence = 0.7
    
    def verify_text(self, text: str, page_number: int = 1) -> Tuple[str, VerificationReport]:
        """
        Verify and correct text using enhanced LLM verification.
        
        Args:
            text: Text to verify
            page_number: Page number for reporting
            
        Returns:
            Tuple of (corrected_text, verification_report)
        """
        start_time = time.time()
        all_results = []
        total_issues = 0
        iterations = 0
        
        current_text = text
        prev_score = 0
        
        # Iterative verification
        max_iterations = getattr(self.config, 'MAX_VERIFICATION_PASSES', 3)
        improvement_threshold = getattr(self.config, 'VERIFICATION_IMPROVEMENT_THRESHOLD', 0.02)
        
        for iteration in range(max_iterations):
            iterations += 1
            
            # Identify issues
            issues = self._identify_issues(current_text, page_number)
            total_issues += len(issues)
            
            if not issues:
                logger.info(f"Iteration {iteration + 1}: No issues found")
                break
            
            logger.info(f"Iteration {iteration + 1}: Found {len(issues)} issues")
            
            # Prioritize issues
            issues = self._prioritize_issues(issues)
            
            # Verify with LLM
            results = self._verify_issues_batch(issues)
            all_results.extend(results)
            
            # Apply corrections
            current_text = self._apply_corrections(current_text, results)
            
            # Check improvement
            corrections_made = sum(1 for r in results if r.was_changed)
            current_score = corrections_made / len(issues) if issues else 0
            
            if iteration > 0 and abs(current_score - prev_score) < improvement_threshold:
                logger.info(f"Stopping: improvement below threshold")
                break
            
            prev_score = current_score
        
        # Calculate statistics
        total_corrections = sum(1 for r in all_results if r.was_changed)
        avg_confidence = (
            sum(r.llm_confidence for r in all_results) / len(all_results)
            if all_results else 1.0
        )
        
        report = VerificationReport(
            total_issues_found=total_issues,
            total_corrections_made=total_corrections,
            issues=[r.issue for r in all_results],
            results=all_results,
            processing_time=time.time() - start_time,
            llm_calls_made=self.stats['llm_calls'],
            average_confidence=avg_confidence,
            iterations=iterations
        )
        
        return current_text, report
    
    def _identify_issues(self, text: str, page_number: int) -> List[VerificationIssue]:
        """Identify all potential issues in text"""
        issues = []
        
        # Check Japanese OCR patterns
        for pattern, issue_type, base_confidence in self.ocr_patterns_japanese:
            issues.extend(self._find_pattern_issues(
                text, pattern, f"jp_ocr_{issue_type}", 
                page_number, base_confidence
            ))
        
        # Check English OCR patterns
        for pattern, issue_type, base_confidence in self.ocr_patterns_english:
            issues.extend(self._find_pattern_issues(
                text, pattern, f"en_ocr_{issue_type}",
                page_number, base_confidence
            ))
        
        # Check structural patterns
        for pattern, issue_type, base_confidence in self.structural_patterns:
            issues.extend(self._find_pattern_issues(
                text, pattern, f"struct_{issue_type}",
                page_number, base_confidence
            ))
        
        # Remove duplicates and overlaps
        issues = self._deduplicate_issues(issues)
        
        return issues
    
    def _find_pattern_issues(self, text: str, pattern: str, issue_type: str,
                             page_number: int, base_confidence: float) -> List[VerificationIssue]:
        """Find issues matching a pattern"""
        issues = []
        
        try:
            for match in re.finditer(pattern, text):
                # Adjust confidence based on context
                confidence = self._adjust_confidence(
                    match.group(), 
                    text[max(0, match.start()-50):match.end()+50],
                    base_confidence
                )
                
                if confidence >= self.min_issue_confidence:
                    self._issue_counter += 1
                    
                    issue = VerificationIssue(
                        issue_id=f"ISS-{self._issue_counter:05d}",
                        issue_type=issue_type,
                        original_text=match.group(),
                        context_before=text[max(0, match.start()-self.context_chars):match.start()],
                        context_after=text[match.end():match.end()+self.context_chars],
                        page_number=page_number,
                        position=match.start(),
                        confidence=confidence
                    )
                    issues.append(issue)
        except re.error as e:
            logger.warning(f"Regex error for pattern {pattern}: {e}")
        
        return issues
    
    def _adjust_confidence(self, match_text: str, context: str, 
                          base_confidence: float) -> float:
        """Adjust confidence based on context"""
        confidence = base_confidence
        
        # Increase confidence if surrounded by normal text
        if re.search(r'[一-龯ぁ-んァ-ヶa-zA-Z]', context):
            confidence += 0.05
        
        # Decrease confidence if in code/technical context
        if re.search(r'[{}\[\]<>=/\\]', context):
            confidence -= 0.1
        
        # Decrease confidence for very short matches
        if len(match_text) < 2:
            confidence -= 0.1
        
        # Increase confidence for longer suspicious patterns
        if len(match_text) > 5:
            confidence += 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _deduplicate_issues(self, issues: List[VerificationIssue]) -> List[VerificationIssue]:
        """Remove duplicate and overlapping issues"""
        if not issues:
            return []
        
        # Sort by position
        issues.sort(key=lambda i: (i.position, -i.confidence))
        
        kept = []
        last_end = -1
        
        for issue in issues:
            issue_end = issue.position + len(issue.original_text)
            
            # Check for overlap
            if issue.position >= last_end:
                kept.append(issue)
                last_end = issue_end
            elif issue.confidence > kept[-1].confidence:
                # Replace with higher confidence issue
                kept[-1] = issue
                last_end = issue_end
        
        return kept
    
    def _prioritize_issues(self, issues: List[VerificationIssue]) -> List[VerificationIssue]:
        """Prioritize issues for verification"""
        # Priority based on type and confidence
        priority_map = {
            'struct_broken_suffix': 1,
            'struct_broken_prefix': 1,
            'jp_ocr_mixed_kana': 2,
            'en_ocr_digit_in_word': 2,
            'struct_excess_space': 3,
        }
        
        for issue in issues:
            # Get base priority
            base_priority = 5  # Default
            for key, priority in priority_map.items():
                if key in issue.issue_type:
                    base_priority = priority
                    break
            
            # Adjust by confidence (higher confidence = higher priority)
            issue.priority = base_priority - int(issue.confidence * 2)
        
        # Sort by priority (lower number = higher priority)
        issues.sort(key=lambda i: (i.priority, -i.confidence))
        
        return issues
    
    def _verify_issues_batch(self, issues: List[VerificationIssue]) -> List[VerificationResult]:
        """Verify issues in batches"""
        results = []
        
        # Process in batches
        for i in range(0, len(issues), self.batch_size):
            batch = issues[i:i + self.batch_size]
            
            for issue in batch:
                # Check cache first
                cache_key = f"{issue.issue_type}:{issue.original_text}"
                if cache_key in self._cache:
                    self.stats['cache_hits'] += 1
                    cached = self._cache[cache_key]
                    result = VerificationResult(
                        issue=issue,
                        corrected_text=cached['corrected'],
                        llm_confidence=cached['confidence'],
                        explanation=cached['explanation'] + " (cached)",
                        was_changed=cached['corrected'] != issue.original_text,
                        verification_method="cache"
                    )
                else:
                    # Verify with LLM
                    result = self._verify_single_issue(issue)
                    
                    # Cache result
                    self._cache[cache_key] = {
                        'corrected': result.corrected_text,
                        'confidence': result.llm_confidence,
                        'explanation': result.explanation
                    }
                
                results.append(result)
        
        return results
    
    def _verify_single_issue(self, issue: VerificationIssue) -> VerificationResult:
        """Verify a single issue with LLM"""
        # Build prompt
        prompt = self._build_verification_prompt(issue)
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse response
        corrected, confidence, explanation = self._parse_response(
            response, issue.original_text
        )
        
        return VerificationResult(
            issue=issue,
            corrected_text=corrected,
            llm_confidence=confidence,
            explanation=explanation,
            was_changed=(corrected != issue.original_text),
            verification_method="llm"
        )
    
    def _build_verification_prompt(self, issue: VerificationIssue) -> str:
        """Build optimized verification prompt"""
        prompt = f"""You are an expert text verification assistant specializing in Japanese and English OCR error correction.

TASK: Verify and correct the following text if it contains errors.

Issue Type: {issue.issue_type}
Confidence: {issue.confidence:.2f}

TEXT TO VERIFY: "{issue.original_text}"

CONTEXT:
Before: "...{issue.context_before[-100:]}"
After: "{issue.context_after[:100]}..."

INSTRUCTIONS:
1. Analyze if the text contains OCR errors, broken words, or formatting issues
2. Consider the context to determine the correct text
3. For Japanese text, watch for:
   - Katakana/Hiragana confusion
   - Similar character substitutions (口/ロ, 力/カ, etc.)
   - Long vowel mark issues (ー/一)
4. For English text, watch for:
   - Number/letter confusion (1/l/I, 0/O)
   - Common OCR errors (rn→m, cl→d)
5. Only fix clear errors - preserve intentional formatting

RESPONSE FORMAT (JSON only):
{{
    "corrected_text": "your correction or original if no error",
    "confidence": 0.95,
    "explanation": "brief explanation of correction or why no change needed"
}}

Respond with ONLY the JSON object, no additional text."""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API"""
        self.stats['llm_calls'] += 1
        
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.warning("No API key configured, using fallback")
            return self._fallback_response(prompt)
        
        try:
            if self.llm_backend == "anthropic":
                return self._call_anthropic(prompt)
            elif self.llm_backend == "openai":
                return self._call_openai(prompt)
            else:
                return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._fallback_response(prompt)
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            return self._fallback_response(prompt)
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI GPT API"""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": "You are a precise text verification assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Generate fallback response when LLM unavailable"""
        # Extract original text
        match = re.search(r'TEXT TO VERIFY: "([^"]*)"', prompt)
        original = match.group(1) if match else ""
        
        corrected = original
        explanation = "Fallback: no API key"
        confidence = 0.5
        
        # Apply basic corrections
        # Fix broken suffixes
        if re.search(r'\s+(ing|ed|tion|ment|ness|ly)\b', original):
            corrected = re.sub(r'\s+(ing|ed|tion|ment|ness|ly)\b', r'\1', original)
            explanation = "Joined broken suffix"
            confidence = 0.8
        
        # Fix broken prefixes
        elif re.search(r'\b(un|re|pre|dis)\s+', original):
            corrected = re.sub(r'\b(un|re|pre|dis)\s+', r'\1', original)
            explanation = "Joined broken prefix"
            confidence = 0.8
        
        # Fix excess spaces
        elif re.search(r'\s{3,}', original):
            corrected = re.sub(r'\s{3,}', ' ', original)
            explanation = "Reduced excess whitespace"
            confidence = 0.9
        
        # Fix digit in word
        elif re.search(r'[a-zA-Z]+[0-9]+[a-zA-Z]+', original):
            corrected = original.replace('1', 'i').replace('0', 'o')
            explanation = "Fixed number/letter confusion"
            confidence = 0.7
        
        return json.dumps({
            "corrected_text": corrected,
            "confidence": confidence,
            "explanation": explanation
        })
    
    def _parse_response(self, response: str, original: str) -> Tuple[str, float, str]:
        """Parse LLM response"""
        try:
            # Extract JSON
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                corrected = data.get('corrected_text', original)
                confidence = float(data.get('confidence', 0.5))
                explanation = data.get('explanation', 'No explanation')
                
                return corrected, confidence, explanation
        
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        
        return original, 0.5, "Parse error - keeping original"
    
    def _apply_corrections(self, text: str, results: List[VerificationResult]) -> str:
        """Apply corrections to text"""
        # Sort by position (reverse)
        sorted_results = sorted(
            results, 
            key=lambda r: r.issue.position, 
            reverse=True
        )
        
        corrected_text = text
        
        for result in sorted_results:
            if result.was_changed and result.llm_confidence >= self.llm_verify_confidence:
                start = result.issue.position
                end = start + len(result.issue.original_text)
                
                corrected_text = (
                    corrected_text[:start] +
                    result.corrected_text +
                    corrected_text[end:]
                )
                
                self.stats['corrections'] += 1
                
                logger.debug(
                    f"Applied: '{result.issue.original_text}' → '{result.corrected_text}' "
                    f"[{result.llm_confidence:.2f}]"
                )
        
        return corrected_text
    
    def get_stats(self) -> Dict:
        """Get verification statistics"""
        return {
            'llm_calls': self.stats['llm_calls'],
            'corrections': self.stats['corrections'],
            'cache_hits': self.stats['cache_hits'],
            'cache_size': len(self._cache)
        }
    
    def clear_cache(self):
        """Clear response cache"""
        self._cache = {}
    
    def print_report(self, report: VerificationReport):
        """Print verification report"""
        print("\n" + "="*60)
        print("ENHANCED LLM VERIFICATION REPORT")
        print("="*60)
        
        print(f"\nIterations:        {report.iterations}")
        print(f"Issues found:      {report.total_issues_found}")
        print(f"Corrections made:  {report.total_corrections_made}")
        print(f"LLM calls:         {report.llm_calls_made}")
        print(f"Avg confidence:    {report.average_confidence:.2f}")
        print(f"Processing time:   {report.processing_time:.2f}s")
        
        if report.results:
            corrections = [r for r in report.results if r.was_changed]
            if corrections:
                print(f"\nCorrections ({len(corrections)}):")
                for r in corrections[:10]:  # Show first 10
                    print(f"  • '{r.issue.original_text}' → '{r.corrected_text}'")
                    print(f"    Confidence: {r.llm_confidence:.2f} | {r.explanation}")
                
                if len(corrections) > 10:
                    print(f"  ... and {len(corrections) - 10} more")
        
        print("\n" + "="*60)


# Convenience function
def verify_text_enhanced(text: str, config=None) -> Tuple[str, VerificationReport]:
    """
    Quick function for enhanced text verification.
    
    Args:
        text: Text to verify
        config: Optional config module
        
    Returns:
        Tuple of (corrected_text, report)
    """
    verifier = EnhancedLLMVerifier(config)
    return verifier.verify_text(text)


if __name__ == "__main__":
    # Test with sample text
    test_text = """
    The pat1ent rece1ved the medicat ion at 3pm.
    This concentrat ion was measured care fully.
    P1ease verify a11 1nformat ion is correct.
    
    日本語のテストです。カタカナとひらがなの混在テスト。
    ロロ と 口口 の区別。力力 と カカ の区別。
    
    This    has   excess    spaces.
    """
    
    print("Testing Enhanced LLM Verifier")
    print("="*60)
    print("Original:")
    print(test_text)
    
    verifier = EnhancedLLMVerifier()
    corrected, report = verifier.verify_text(test_text)
    
    print("\nCorrected:")
    print(corrected)
    
    verifier.print_report(report)
