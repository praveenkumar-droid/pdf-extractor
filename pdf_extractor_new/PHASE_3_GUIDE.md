# PHASE 3: FIX EXTRACTION RULES - IMPLEMENTATION GUIDE

**Status:** Ready to Implement  
**Time Required:** 8-10 hours  
**Priority:** CRITICAL

---

## PROBLEM ANALYSIS

### Current Issue: Over-Filtering

Your current code removes content that should be kept:

```python
# extractor.py line 38-44
self.header_footer_patterns = [
    r'^\d+$',  # PROBLEM: Catches "5" (page) AND "1" (section)
    r'^-\s*\d+\s*-$',
    r'^ページ\s*\d+',
    r'^Page\s*\d+',
    r'^\d+\s*/\s*\d+$',
]
```

**What Gets WRONGLY Removed:**
- "1" at start of section 1
- "2" at start of section 2
- Section numbers like "1.2", "3.1.4" (if split)
- Footnote numbers *1, *2

**What SHOULD Be Removed:**
- "5" in top corner (actual page number)
- "Page 5" in header/footer
- Isolated page numbers

---

## SOLUTION: SMART DETECTION

### Key Principle: Context-Aware Filtering

Instead of removing based on pattern alone, consider:
1. **Position** - Where is it on the page?
2. **Context** - What text is nearby?
3. **Formatting** - Font size, style
4. **Pattern** - Does it have decimal points?

### Decision Tree:

```
Text = "1.2"
├─ Has decimal point? YES → Section number → KEEP ✓
└─ NO → Check position...

Text = "5"
├─ In corner/margin? YES → Check if isolated
│  ├─ No text nearby? YES → Page number → REMOVE ✓
│  └─ Text nearby? NO → Might be content → KEEP ✓
└─ In main content? YES → KEEP ✓

Text = "1"
├─ Followed by heading/text? YES → Section start → KEEP ✓
├─ In corner alone? YES → Page number → REMOVE ✓
└─ In margin? YES → Check if repeated across pages
```

---

## IMPLEMENTATION APPROACH

We'll create a new, smarter filtering system with these components:

### 1. Enhanced Pattern Recognition
- Distinguish section numbers from page numbers
- Recognize footnote markers
- Identify content vs metadata

### 2. Context-Aware Logic
- Check surrounding text
- Consider position on page
- Look at font size (if available)

### 3. "Include by Default"
- When uncertain, KEEP the text
- Only remove if confident it's metadata

---

## FILES TO MODIFY

### File 1: extractor.py
**Sections to change:**
1. `__init__` - Add better patterns (lines 38-44)
2. `_filter_metadata` - Smarter filtering logic (lines 154-179)
3. Add new method: `_is_section_number`
4. Add new method: `_is_page_number_not_content`
5. Add new method: `_has_nearby_content`

### File 2: config.py (optional)
**New settings to add:**
- `INCLUDE_SECTION_NUMBERS = True`
- `INCLUDE_FOOTNOTE_MARKERS = True`
- `AGGRESSIVE_FILTERING = False` (for "include by default")

---

## IMPLEMENTATION PLAN

### Step 1: Add New Helper Methods (2 hours)

```python
def _is_section_number(self, text: str) -> bool:
    """
    Detect if text is a section number that should be kept.
    
    Section numbers include:
    - 1.2, 3.1.4 (decimal notation)
    - (1), (2) (parentheses)
    - ①, ②, ③ (circled numbers)
    - 1), 2) (closing parenthesis)
    - 1., 2. (period after number)
    
    Returns True if it's a section number (KEEP IT)
    """
    pass

def _is_page_number_not_content(self, text: str, word: Dict, page_height: float, all_words: List[Dict]) -> bool:
    """
    Determine if text is a page number (REMOVE) vs content (KEEP).
    
    Page number indicators:
    - Single digit in corner/margin
    - Isolated with no nearby text
    - In top 5% or bottom 5% of page
    - Matches pattern: "Page N", "ページ N"
    
    Returns True if it's definitely a page number (REMOVE IT)
    Returns False if it might be content (KEEP IT)
    """
    pass

def _has_nearby_content(self, word: Dict, all_words: List[Dict], distance: float = 50) -> bool:
    """
    Check if there's other text near this word.
    
    If isolated (no nearby text) → might be page number
    If has nearby text → likely content
    """
    pass
```

### Step 2: Update Pattern Definitions (1 hour)

```python
# In __init__, replace header_footer_patterns with more specific ones:

# STRICT page number patterns (definitely remove)
self.strict_page_patterns = [
    r'^Page\s+\d+$',           # "Page 5"
    r'^ページ\s*\d+$',          # "ページ 5"
    r'^-\s*\d+\s*-$',          # "- 5 -"
    r'^\d+\s*/\s*\d+$',        # "5 / 100"
]

# Section number patterns (definitely keep)
self.section_patterns = [
    r'^\d+\.\d+',              # 1.2, 3.1.4
    r'^\(\d+\)',               # (1), (2)
    r'^[①-⑳]',                 # ①, ②, ③
    r'^\d+[)）]',               # 1), 2)
    r'^\d+\.',                 # 1., 2. (but check if followed by text)
]

# Footnote markers (definitely keep)
self.footnote_markers = [
    r'^\*\d+',                 # *1, *2
    r'^※\d*',                  # ※, ※1
    r'^注\d*',                  # 注, 注1
    r'^†',                     # †
    r'^‡',                     # ‡
    r'^\[\d+\]',               # [1], [2]
]
```

### Step 3: Rewrite _filter_metadata (3 hours)

```python
def _filter_metadata(self, words: List[Dict], headers: List[str], 
                     footers: List[str], page_height: float) -> List[Dict]:
    """
    Remove headers, footers, and page numbers.
    
    NEW APPROACH: Include by default, only remove when certain.
    """
    filtered = []
    
    for i, word in enumerate(words):
        text = word['text'].strip()
        
        # RULE 1: Keep section numbers (definite content)
        if self._is_section_number(text):
            filtered.append(word)
            continue
        
        # RULE 2: Keep footnote markers (definite content)
        if any(re.match(pattern, text) for pattern in self.footnote_markers):
            filtered.append(word)
            continue
        
        # RULE 3: Remove strict page number patterns
        if config.REMOVE_PAGE_NUMBERS:
            if any(re.match(pattern, text) for pattern in self.strict_page_patterns):
                continue
        
        # RULE 4: Remove detected repeating elements
        if config.REMOVE_HEADERS_FOOTERS:
            if text in headers or text in footers:
                continue
        
        # RULE 5: Check if single digit in margin (might be page number)
        if re.match(r'^\d+$', text):  # Single digit only
            if self._is_page_number_not_content(text, word, page_height, words):
                continue  # Remove as page number
            # Otherwise, keep it (might be section start)
        
        # RULE 6: Skip content in extreme margins only
        if word['top'] < page_height * 0.03:  # Top 3% (narrower than before)
            continue
        if word['top'] > page_height * 0.97:  # Bottom 3% (narrower than before)
            continue
        
        # DEFAULT: KEEP IT (include by default)
        filtered.append(word)
    
    return filtered
```

### Step 4: Implement Helper Methods (2 hours)

Full implementation of the three helper methods.

### Step 5: Testing (2 hours)

Test on various PDFs to ensure:
- Section numbers are kept
- Page numbers are removed
- Footnotes are kept
- No false positives

---

## EXPECTED RESULTS

### Before (Current):
```
PDF: "1. Introduction\n1.2 Background"
Extracted: "Introduction\nBackground"  ❌ Lost section numbers!

PDF: "See note *1 below"
Extracted: "See note below"  ❌ Lost footnote marker!
```

### After (Fixed):
```
PDF: "1. Introduction\n1.2 Background"
Extracted: "1. Introduction\n1.2 Background"  ✓ Kept section numbers!

PDF: "See note *1 below"
Extracted: "See note *1 below"  ✓ Kept footnote marker!

PDF: Corner has "5" (page number)
Extracted: (removed correctly)  ✓ Removed page number!
```

---

## TESTING STRATEGY

### Test Set 1: Section Numbers
- [ ] "1." followed by text → KEEP
- [ ] "1.2" anywhere → KEEP
- [ ] "3.1.4" anywhere → KEEP
- [ ] "(1)" anywhere → KEEP
- [ ] "①" anywhere → KEEP

### Test Set 2: Page Numbers
- [ ] "5" in corner alone → REMOVE
- [ ] "Page 5" in header → REMOVE
- [ ] "ページ 5" in header → REMOVE

### Test Set 3: Footnotes
- [ ] "*1" in text → KEEP
- [ ] "※" in text → KEEP
- [ ] "注1" in text → KEEP

### Test Set 4: Edge Cases
- [ ] "1" at start of section → KEEP
- [ ] "1" in corner → REMOVE
- [ ] "2" in middle of text → KEEP

---

## READY TO IMPLEMENT?

I'll now create the complete fixed extractor.py with all the improvements.

**Shall I proceed with creating the code?**
