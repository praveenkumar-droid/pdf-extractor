# PHASE 4: CHARACTER PRESERVATION - IMPLEMENTATION GUIDE

**Status:** ✅ Ready to Implement  
**Time Required:** 2-3 hours  
**Priority:** CRITICAL (Fixes core violation)

---

## PROBLEM

Your current code VIOLATES the fundamental rule:
```
"EXTRACT ONLY - NEVER TRANSFORM: Extract characters EXACTLY 
as they appear. Do NOT convert, normalize, or transform any characters."
```

**Current Code Issues:**
1. Normalizes half-width → full-width (lines 15-19)
2. Converts katakana (lines 22-24)
3. Transforms characters during cleanup (line 248)

---

## SOLUTION

Remove ALL character transformation/normalization while keeping:
- ✅ Line joining logic (good)
- ✅ Spacing fixes (optional, configurable)
- ✅ Punctuation cleanup (optional, configurable)

---

## CHANGES TO MAKE

### 1. Update `config.py`

Change this line:
```python
# OLD (line 29):
NORMALIZE_CHARACTERS = True  # Convert half-width to full-width

# NEW:
NORMALIZE_CHARACTERS = False  # DISABLED - Preserve characters exactly
```

And add a note:
```python
# Character normalization - DISABLED per LLM extraction specs
# Rule: "EXTRACT ONLY - NEVER TRANSFORM"
# All characters must be preserved exactly as they appear in PDF
NORMALIZE_CHARACTERS = False  # DO NOT ENABLE - Violates extraction rules
NORMALIZE_KATAKANA = False   # DO NOT ENABLE - Violates extraction rules
```

### 2. Update `extractor.py` - Remove Normalization Code

**Option A: Comment Out (Recommended for now)**
Keep the code but disable it, in case you need it later:

```python
# Lines 15-24 - Comment out like this:
def __init__(self):
    self.column_gap = config.COLUMN_GAP_THRESHOLD
    self.line_height = config.LINE_HEIGHT_THRESHOLD
    
    # DISABLED: Character normalization violates "EXTRACT ONLY - NEVER TRANSFORM" rule
    # These mappings are kept but unused - all characters are preserved exactly
    # 
    # # Character normalization map (half-width to full-width)
    # self.half_to_full = str.maketrans(
    #     '0123456789()[].,',
    #     '０１２３４５６７８９（）［］．，'
    # )
    # 
    # # Half-width to full-width katakana
    # self.half_kata = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝ'
    # self.full_kata = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン'
    # self.kata_trans = str.maketrans(self.half_kata, self.full_kata)
    
    # ... rest of __init__ ...
```

**Option B: Delete Completely (Clean approach)**
Simply remove lines 15-24 entirely.

### 3. Update `_cleanup_text` method (line 210)

Change the logic to skip normalization:

```python
def _cleanup_text(self, text: str) -> str:
    """
    Apply minimal cleanup - NO CHARACTER TRANSFORMATION
    
    Per LLM extraction specs: "EXTRACT ONLY - NEVER TRANSFORM"
    Characters are preserved exactly as they appear in PDF
    """
    # REMOVED: Character normalization (violates extraction rules)
    # if config.NORMALIZE_CHARACTERS:
    #     text = self._normalize_characters(text)
    
    # Optional spacing fixes (can be disabled via config)
    if config.FIX_SPACING:
        text = self._fix_spacing(text)
    
    # Optional line joining (preserves content structure)
    if config.JOIN_LINES:
        text = self._join_lines(text)
    
    # Optional punctuation cleanup (minimal changes)
    if config.FIX_PUNCTUATION:
        text = self._fix_punctuation(text)
    
    # Remove excessive blank lines only
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    return text.strip()
```

### 4. Update or Remove `_normalize_characters` method (line 235)

**Option A: Mark as deprecated:**
```python
def _normalize_characters(self, text: str) -> str:
    """
    DEPRECATED: Character normalization violates extraction rules
    
    This method is kept for reference but should NOT be used.
    Per LLM specs: "EXTRACT ONLY - NEVER TRANSFORM"
    """
    # This method is now disabled and will not be called
    return text  # Return unchanged
```

**Option B: Delete entirely** (recommended)

### 5. Add Documentation Note

Add this to the class docstring:

```python
class JapanesePDFExtractor:
    """
    Extracts text from Japanese PDFs in perfect visual reading order
    
    CRITICAL PRINCIPLE: "EXTRACT ONLY - NEVER TRANSFORM"
    - All characters are preserved exactly as they appear
    - No half-width to full-width conversion
    - No katakana normalization
    - No character transformations of any kind
    
    Only minimal cleanup is applied:
    - Line joining (configurable)
    - Spacing fixes (configurable)
    - Punctuation deduplication (configurable)
    """
```

---

## TESTING

After making changes, test with PDFs that have:

1. **Mixed Width Characters:**
   ```
   PDF contains: "ABC123" (half-width)
   Should extract: "ABC123" (half-width) ✓
   NOT: "ＡＢＣ１２３" (full-width) ✗
   ```

2. **Mixed Katakana:**
   ```
   PDF contains: "ｱｲｳｴｵ" (half-width)
   Should extract: "ｱｲｳｴｵ" (half-width) ✓
   NOT: "アイウエオ" (full-width) ✗
   ```

3. **Chemical Formulas:**
   ```
   PDF contains: "H2O" or "H₂O"
   Should extract: Exactly as appears ✓
   ```

---

## IMPLEMENTATION CHECKLIST

- [ ] Update config.py (set NORMALIZE_CHARACTERS = False)
- [ ] Comment out or remove normalization maps in __init__
- [ ] Update _cleanup_text to skip normalization
- [ ] Update/remove _normalize_characters method
- [ ] Add documentation note to class docstring
- [ ] Test with mixed-width PDF
- [ ] Test with half-width katakana PDF
- [ ] Verify no character transformation occurs
- [ ] Commit changes with message: "Phase 4: Remove character normalization to preserve fidelity"

---

## READY TO IMPLEMENT?

The changes are straightforward:
1. Set config flag to False
2. Comment out or remove normalization code
3. Update cleanup method
4. Test

**Estimated time:** 30 minutes to make changes, 1-2 hours for testing

**Let me know when you're ready and I'll provide the complete updated files!**
