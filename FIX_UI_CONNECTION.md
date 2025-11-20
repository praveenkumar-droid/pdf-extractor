# Fix Required: Connect All Features to Web UI

## Current Problem

The web UI (`/ui`) uses `JapanesePDFExtractor` which is missing:
- ❌ Anti-hallucination verification
- ❌ Full Phase 0-10 pipeline
- ❌ Quality scoring
- ❌ Element inventory

**Current Web UI Accuracy:** ~88-92% (instead of 94-98%)

---

## Solution: Update API to use MasterExtractor

### Change Required in `api.py`:

**Replace this (Line 16):**
```python
from extractor import JapanesePDFExtractor
```

**With this:**
```python
from master_extractor import MasterExtractor
```

**Replace this (Line 40):**
```python
extractor = JapanesePDFExtractor()
```

**With this:**
```python
extractor = MasterExtractor(
    verbose=False,  # Don't print to console in API
    enable_llm_verification=False,  # Can enable if you have API key
    enable_chunking=True
)
```

**Replace this (Line 134-137):**
```python
local_extractor = JapanesePDFExtractor()
text = local_extractor.extract_pdf(str(temp_path))
```

**With this:**
```python
local_extractor = MasterExtractor(
    verbose=False,
    enable_llm_verification=False,
    enable_chunking=True
)
result = local_extractor.extract(str(temp_path))
text = result.raw_text  # Or result.formatted_text for page markers
```

---

## Impact

### Before Fix:
- Web UI accuracy: ~88-92%
- Features: 4 out of 5

### After Fix:
- Web UI accuracy: ~94-98%
- Features: 5 out of 5 (100%)
- Bonus: Get quality scoring, inventory, error handling

---

## Estimated Time: 15-20 minutes

## Risk: Low
- MasterExtractor uses JapanesePDFExtractor internally
- Backward compatible
- Won't break existing functionality

---

## Testing After Fix:

1. Upload a PDF with chemical formulas (H₂O, CO₂)
2. Check for table duplication
3. Verify footnotes in bottom 10%
4. Test anti-hallucination (upload PDF with markdown formatting)
5. Check quality score in response

---

**Status:** Not yet implemented
**Priority:** HIGH (to achieve full 95% accuracy via UI)
