# PHASE 5: LLM VERIFICATION SYSTEM - COMPLETE GUIDE

**Status:** ✅ Module created  
**File:** D:\pdf_extractor_new\llm_verifier.py  
**Time:** 3-4 hours (testing + integration)

---

## WHAT'S BEEN CREATED

### New Module: llm_verifier.py

**Purpose:** Use LLM intelligence to verify and correct extraction errors that rule-based systems miss.

**Components:**
1. **VerificationIssue** - Identified problem in text
2. **VerificationResult** - LLM's correction
3. **VerificationReport** - Complete verification summary
4. **LLMVerifier** - Main verification class
5. **verify_extracted_text()** - Convenience function

---

## SUPPORTED LLM BACKENDS

| Backend | Description | Configuration |
|---------|-------------|---------------|
| `mock` | Testing mode (no API calls) | Default, no key needed |
| `openai` | OpenAI GPT-4/3.5 | Requires API key |
| `anthropic` | Anthropic Claude | Requires API key |
| `local` | Local models (Ollama, etc.) | Runs on localhost:11434 |

---

## QUICK START - TEST IN 5 MINUTES

### Test 1: Mock Mode (No API Key)
```python
from llm_verifier import LLMVerifier

# Create verifier (mock mode for testing)
verifier = LLMVerifier(llm_backend="mock")

# Text with errors
text = """
The pat1ent rece1ved the medicat ion at 3pm.
The concentrat ion was 5%.
"""

# Verify
corrected, report = verifier.verify_text(text)

# Show results
print("Original:", text)
print("Corrected:", corrected)
verifier.print_report(report)
```

**Expected Output:**
```
Original:
The pat1ent rece1ved the medicat ion at 3pm.
The concentrat ion was 5%.

Corrected:
The patient received the medication at 3pm.
The concentration was 5%.

============================================================
LLM VERIFICATION REPORT
============================================================

Issues found:      4
Corrections made:  4
LLM calls:         4
Processing time:   0.01s
Avg confidence:    0.88

Corrections made:
  • 'pat1ent' → 'patient'
    Type: ocr_digit_in_word
    Confidence: 0.85
    Reason: Fixed OCR digit-letter confusion

  • 'rece1ved' → 'received'
    Type: ocr_digit_in_word
    Confidence: 0.85
    Reason: Fixed OCR digit-letter confusion
============================================================
```

### Test 2: With OpenAI
```python
from llm_verifier import LLMVerifier

verifier = LLMVerifier(
    llm_backend="openai",
    api_key="your-openai-api-key",
    model="gpt-4"
)

corrected, report = verifier.verify_text(text)
```

### Test 3: With Anthropic Claude
```python
from llm_verifier import LLMVerifier

verifier = LLMVerifier(
    llm_backend="anthropic",
    api_key="your-anthropic-api-key",
    model="claude-3-sonnet-20240229"
)

corrected, report = verifier.verify_text(text)
```

### Test 4: With Local Model (Ollama)
```python
from llm_verifier import LLMVerifier

verifier = LLMVerifier(
    llm_backend="local",
    model="llama2"  # or any model you have in Ollama
)

corrected, report = verifier.verify_text(text)
```

---

## WHAT IT DETECTS & FIXES

### ✅ OCR Errors:
```
pat1ent → patient       (digit in word)
rece1ved → received     (1 as i)
s0lution → solution     (0 as o)
```

### ✅ Broken Words:
```
concentrat ion → concentration   (suffix split)
un able → unable                 (prefix split)
hyph-
enated → hyphenated              (line break)
```

### ✅ Ambiguous Characters:
```
I11 → Ill or 111    (context-dependent)
O00 → OOO or 000    (context-dependent)
```

### ✅ Formatting Issues:
```
too    many    spaces → too many spaces
。。。 → 。    (duplicate punctuation)
```

---

## HOW IT WORKS

### Step 1: Issue Detection
```python
# Patterns to find potential issues
ocr_patterns = [
    r'[a-z][0-9][a-z]',     # pat1ent
    r'rn(?=[a-z])',          # rn as m
]

broken_patterns = [
    r'\w+\s+(?:ing|ed|tion)', # concentrat ion
    r'\b(?:un|re)\s+\w+',     # un able
]
```

### Step 2: Context Gathering
```
For each issue, get:
- 100 chars before
- The problematic text
- 100 chars after
```

### Step 3: LLM Verification
```
Send to LLM:
- Issue type
- Original text
- Context
- Instructions

Get back:
- Corrected text
- Confidence score
- Explanation
```

### Step 4: Apply Corrections
```
Only apply if:
- LLM confidence >= 0.7
- Text was actually changed
- No conflicting corrections
```

---

## VERIFICATION REPORT

```python
report = VerificationReport(
    total_issues_found=10,      # Issues detected
    total_corrections_made=7,    # Actually changed
    issues=[...],               # All issues found
    results=[...],              # All LLM responses
    processing_time=2.5,        # Seconds
    llm_calls_made=10,          # API calls
    average_confidence=0.85     # Avg LLM confidence
)

# Export as dictionary
report_dict = report.to_dict()
```

---

## INTEGRATION WITH MASTER EXTRACTOR

Add to master_extractor.py:

```python
# Add import
from llm_verifier import LLMVerifier

# In MasterExtractor.__init__:
self.llm_verifier = LLMVerifier(
    llm_backend="mock",  # Change to "openai" etc. for production
    api_key=None         # Add your API key
)

# In extract() method, after all extraction:

# ═══════════════════════════════════════════════════════════
# PHASE 5: LLM VERIFICATION
# ═══════════════════════════════════════════════════════════
if self.verbose:
    print("\n[Phase 5] LLM verification...")

corrected_text, verification_report = self.llm_verifier.verify_text(raw_text)

if self.verbose:
    print(f"  → Found {verification_report.total_issues_found} issues")
    print(f"  → Made {verification_report.total_corrections_made} corrections")
    print(f"  → Avg confidence: {verification_report.average_confidence:.2f}")

# Use corrected_text for output
raw_text = corrected_text
```

---

## CONFIGURATION OPTIONS

### Adjust Sensitivity:
```python
verifier = LLMVerifier()

# More sensitive (catches more issues)
verifier.min_issue_confidence = 0.5

# Less sensitive (fewer false positives)
verifier.min_issue_confidence = 0.8
```

### Adjust Context Window:
```python
# More context for LLM
verifier.context_chars = 200

# Less context (faster)
verifier.context_chars = 50
```

### Adjust Batch Size:
```python
# Larger batches (fewer API calls)
verifier.batch_size = 10

# Smaller batches (more control)
verifier.batch_size = 3
```

### LLM Parameters:
```python
verifier = LLMVerifier(
    model="gpt-4",
    max_tokens=1000,
    temperature=0.1  # Lower = more deterministic
)
```

---

## TRANSPARENCY & AUDIT

### Add Verification Markers:
```python
# Add markers showing what was corrected
marked_text = verifier.add_verification_markers(corrected_text, report)

# Output includes:
"""
The patient received the medication at 3pm.
The concentration was 5%.

────────────────────────────────────────
[LLM VERIFIED: 4 corrections]
Corrections:
  • 'pat1ent' → 'patient'
  • 'rece1ved' → 'received'
  • 'medicat ion' → 'medication'
  • 'concentrat ion' → 'concentration'
"""
```

### Export Report:
```python
# Get as dictionary (for JSON export)
report_dict = report.to_dict()

# Save to file
import json
with open("verification_log.json", "w") as f:
    json.dump(report_dict, f, indent=2)
```

---

## COST CONSIDERATIONS

### API Costs (Approximate):

| Backend | Model | Cost per 1K tokens |
|---------|-------|-------------------|
| OpenAI | GPT-4 | $0.03 input, $0.06 output |
| OpenAI | GPT-3.5 | $0.0005 input, $0.0015 output |
| Anthropic | Claude 3 Sonnet | $0.003 input, $0.015 output |
| Local | Any | Free (compute cost only) |

### Optimization Tips:
1. Use `mock` mode for testing
2. Batch issues together (already implemented)
3. Use GPT-3.5 for simple errors, GPT-4 for complex
4. Set higher `min_issue_confidence` to reduce calls
5. Use local models for privacy-sensitive documents

---

## BEFORE vs AFTER

### Before Phase 5:
```
Extracted text:
"The pat1ent rece1ved the medicat ion.
The concentrat ion was 5%."

← Errors remain, unreadable! ❌
```

### After Phase 5:
```
Verified text:
"The patient received the medication.
The concentration was 5%."

[LLM VERIFIED: 4 corrections]

← Clean, accurate text! ✅
```

---

## TROUBLESHOOTING

### Issue: API key error
```python
# Check your API key
verifier = LLMVerifier(
    llm_backend="openai",
    api_key="sk-..."  # Make sure this is valid
)
```

### Issue: Too many API calls
```python
# Increase batch size
verifier.batch_size = 10

# Increase confidence threshold
verifier.min_issue_confidence = 0.8
```

### Issue: Too many false positives
```python
# Increase confidence threshold
verifier.min_issue_confidence = 0.8

# Or adjust patterns in __init__
```

### Issue: Local model not responding
```python
# Check Ollama is running
# curl http://localhost:11434/api/generate

# Use correct model name
verifier = LLMVerifier(
    llm_backend="local",
    model="llama2"  # Must be pulled in Ollama
)
```

---

## TESTING CHECKLIST

- [ ] llm_verifier.py imports correctly
- [ ] LLMVerifier creates correctly
- [ ] Mock mode works (no API key)
- [ ] Issues detected in sample text
- [ ] Corrections applied correctly
- [ ] Report prints correctly
- [ ] Markers added to output
- [ ] (Optional) OpenAI backend works
- [ ] (Optional) Anthropic backend works
- [ ] (Optional) Local backend works
- [ ] Integration with master_extractor planned

---

## WEEK 2 PROGRESS

```
WEEK 2: Quality Systems (32 hours)
├─ ✅ Phase 2: Layout Intelligence (8h) ← DONE!
├─ ✅ Phase 5: LLM Verification (8h) ← DONE!
├─ ⏭️  Phase 7: Quality Scoring (6h) ← NEXT
├─ ⏭️  Phase 8: Content Classification (4h)
├─ ⏭️  Phase 10: Context Windows (4h)
└─ ⏭️  Phase 11: Confidence Scoring (2h)

Progress: 16/32 hours (50% of Week 2) 🎉
```

---

## SUMMARY

✅ **Created:**
- llm_verifier.py (650+ lines)

✅ **Features:**
- Issue detection (OCR, broken words, formatting)
- Multiple LLM backends (OpenAI, Anthropic, local, mock)
- Contextual verification prompts
- Confidence scoring
- Transparency markers
- Audit trail/logging
- Batch processing

✅ **Backends:**
- Mock (testing)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local (Ollama, LM Studio)

⏱ **Time:**
- Testing (mock): 5 minutes
- API setup: 30 minutes
- Integration: 2-3 hours

---

**Ready to test Phase 5?**

Run:
```python
from llm_verifier import LLMVerifier

verifier = LLMVerifier(llm_backend="mock")
text = "The pat1ent rece1ved medicat ion."
corrected, report = verifier.verify_text(text)
print(corrected)
verifier.print_report(report)
```

Let me know the results! 🚀
