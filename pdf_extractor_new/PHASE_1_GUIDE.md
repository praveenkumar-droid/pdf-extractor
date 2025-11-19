# PHASE 1: SUPERSCRIPT/SUBSCRIPT DETECTION - COMPLETE GUIDE

**Status:** ✅ Module created  
**File:** D:\pdf_extractor_new\superscript_detector.py  
**Time:** 4-6 hours (testing + integration)

---

## WHAT'S BEEN CREATED

### New Module: superscript_detector.py

**Purpose:** Detect superscripts (H²O, x², *¹) and subscripts (H₂O, CO₂) using font analysis.

**Components:**

1. **EnhancedTextElement** - Dataclass with super/subscript flags
2. **SuperscriptSubscriptDetector** - Main detection class
3. **analyze_pdf_scripts()** - Convenience function

---

## DETECTION METHODS

The detector uses **4 methods** to identify super/subscripts:

### Method 1: Font Size Analysis
```
Element size < 70% of average size = likely super/subscript
Example: "H" (12pt) + "2" (6pt) → "2" is subscript
```

### Method 2: Baseline Offset
```
Vertical position offset > 20% = super/subscript
Example: "x" baseline 0, "²" baseline +3pt → superscript
```

### Method 3: Pattern Matching
```
Matches known patterns:
- *1, *2 (footnote markers)
- [1], [2] (references)
- ¹²³ (unicode superscripts)
- ₀₁₂ (unicode subscripts)
```

### Method 4: Context Awareness
```
Chemical context: H + 2 → H₂
Math context: x + 2 → x²
After markers: * + 1 → *¹
```

---

## QUICK START - TEST IN 5 MINUTES

### Test 1: Analyze a Page
```python
from superscript_detector import SuperscriptSubscriptDetector
import pdfplumber

# Create detector
detector = SuperscriptSubscriptDetector()

# Analyze a page
with pdfplumber.open("input/test.pdf") as pdf:
    page = pdf.pages[0]
    elements = detector.analyze_page(page)

# Check results
stats = detector.get_statistics(elements)
detector.print_statistics(stats)

# Show detected scripts
for elem in elements:
    if elem.is_superscript:
        print(f"Superscript found: '{elem.text}' at ({elem.x0:.1f}, {elem.top:.1f})")
    elif elem.is_subscript:
        print(f"Subscript found: '{elem.text}' at ({elem.x0:.1f}, {elem.top:.1f})")
```

**Expected Output:**
```
============================================================
SUPERSCRIPT/SUBSCRIPT DETECTION STATISTICS
============================================================
Total elements:    456
Superscripts:      23 (5.0%)
Subscripts:        12 (2.6%)
Normal text:       421
============================================================

Superscript found: '*1' at (345.2, 123.4)
Superscript found: '2' at (456.7, 234.5)
Subscript found: '2' at (123.4, 345.6)
```

### Test 2: Find Formulas
```python
from superscript_detector import SuperscriptSubscriptDetector
import pdfplumber

detector = SuperscriptSubscriptDetector()

with pdfplumber.open("input/test.pdf") as pdf:
    page = pdf.pages[0]
    elements = detector.analyze_page(page)
    
    # Find chemical/math formulas
    formulas = detector.find_formulas(elements)
    print("Formulas found:", formulas)
```

**Expected Output:**
```
Formulas found: ['H2O', 'CO2', 'x2', 'CH4']
```

### Test 3: Quick Analysis
```python
from superscript_detector import analyze_pdf_scripts

# Analyze entire PDF
results = analyze_pdf_scripts("input/test.pdf")

# Results is dict: {page_num: [elements]}
print(f"Analyzed {len(results)} pages")
```

---

## WHAT IT DETECTS

### ✅ Chemical Formulas:
- H₂O (water)
- CO₂ (carbon dioxide)
- CH₄ (methane)
- H₂SO₄ (sulfuric acid)
- Ca²⁺ (calcium ion)

### ✅ Math Expressions:
- x² (x squared)
- y³ (y cubed)
- a⁴ (a to the fourth)
- 2ⁿ (2 to the n)

### ✅ Footnote Markers:
- *1, *2, *3 (asterisk style)
- ¹, ², ³ (unicode superscripts)
- [1], [2], [3] (bracketed)
- †, ‡ (dagger symbols)

### ✅ Reference Numbers:
- [1], [2], [3]
- (1), (2), (3) when small
- Superscript digits

---

## INTEGRATION WITH EXTRACTOR

To integrate with your main extractor, you have 2 options:

### Option A: Pre-Analysis (Recommended)

Add detection BEFORE extraction to mark super/subscripts:

```python
# In extractor.py, add import:
from superscript_detector import SuperscriptSubscriptDetector

# In JapanesePDFExtractor.__init__:
self.script_detector = SuperscriptSubscriptDetector()

# In _extract_page method, add after getting words:
def _extract_page(self, page, headers, footers):
    # Existing code to get words...
    
    # NEW: Detect super/subscripts
    enhanced_elements = self.script_detector.analyze_page(page)
    
    # Create lookup for super/subscript status
    script_status = {}
    for elem in enhanced_elements:
        key = (elem.x0, elem.top, elem.text)
        script_status[key] = {
            'is_super': elem.is_superscript,
            'is_sub': elem.is_subscript
        }
    
    # Mark words with script status
    for word in words:
        key = (word['x0'], word['top'], word['text'])
        if key in script_status:
            word['is_superscript'] = script_status[key]['is_super']
            word['is_subscript'] = script_status[key]['is_sub']
    
    # Continue with existing extraction...
```

### Option B: Post-Processing (Simpler)

Analyze AFTER extraction to identify missed scripts:

```python
from superscript_detector import analyze_pdf_scripts

# After extraction
text = extractor.extract_pdf("file.pdf")

# Analyze to see what was missed
results = analyze_pdf_scripts("file.pdf")

total_scripts = sum(
    sum(1 for e in elements if e.is_superscript or e.is_subscript)
    for elements in results.values()
)

print(f"Total super/subscripts in PDF: {total_scripts}")
print("Check if they're in extracted text!")
```

---

## EXAMPLE: BEFORE vs AFTER

### Before Phase 1:
```
PDF contains: "H₂O", "CO₂", "x²", "See note *¹"

Extracted:
"H O"       ← Lost the "2"!
"C O"       ← Lost the "2"!
"x"         ← Lost the "2"!
"See note"  ← Lost the "*1"!
```

### After Phase 1:
```
PDF contains: "H₂O", "CO₂", "x²", "See note *¹"

Detected:
- Page 1: 4 subscripts found
- Page 1: 1 superscript found

Elements:
H [normal]
₂ [SUBSCRIPT] ← Detected!
O [normal]
C [normal]
₂ [SUBSCRIPT] ← Detected!
O [normal]
x [normal]
² [SUPERSCRIPT] ← Detected!
*¹ [SUPERSCRIPT] ← Detected!

With proper extraction integration:
"H₂O"       ✓ Preserved!
"CO₂"       ✓ Preserved!
"x²"        ✓ Preserved!
"See note *¹" ✓ Preserved!
```

---

## TESTING SCENARIOS

### Test 1: Chemical Formulas
```python
# Test with chemical formula PDF
from superscript_detector import analyze_pdf_scripts

results = analyze_pdf_scripts("chemical_formulas.pdf")

# Check for H2O, CO2, etc.
for page_num, elements in results.items():
    scripts = [e for e in elements if e.is_subscript]
    print(f"Page {page_num}: {len(scripts)} subscripts")
```

### Test 2: Math Document
```python
# Test with math equations
results = analyze_pdf_scripts("math_document.pdf")

for page_num, elements in results.items():
    supers = [e for e in elements if e.is_superscript]
    print(f"Page {page_num}: {len(supers)} superscripts")
```

### Test 3: Footnoted Document
```python
# Test with footnotes
results = analyze_pdf_scripts("footnote_document.pdf")

# Look for *1, *2, etc.
for page_num, elements in results.items():
    footnotes = [e for e in elements 
                 if e.is_superscript and e.text.startswith('*')]
    print(f"Page {page_num}: {len(footnotes)} footnote markers")
```

---

## STATISTICS INTERPRETATION

### High Superscript Count (>5%):
→ Document has many footnotes or references
→ Or mathematical content
→ Make sure they're being extracted!

### High Subscript Count (>3%):
→ Document has chemical formulas
→ Or scientific notation
→ Make sure they're being preserved!

### Low Counts (<1%):
→ Document may not have super/subscripts
→ Or detection may need tuning
→ Check manually

---

## DETECTION ACCURACY

### What It Detects Well:
✓ Chemical formulas (H₂O, CO₂)
✓ Math expressions (x², y³)
✓ Footnote markers (*1, *2)
✓ Unicode super/subscripts (¹²³, ₀₁₂)
✓ Small text near larger text

### What It May Miss:
⚠ Super/subscripts in same font size as base
⚠ Complex nested expressions
⚠ Unusual formatting
⚠ Hand-drawn or image-based text

### False Positives:
⚠ Very small text that isn't super/subscript
⚠ Numbers in parentheses (1), (2)
⚠ Decorative small text

---

## TUNING PARAMETERS

If detection isn't working well, adjust thresholds:

```python
detector = SuperscriptSubscriptDetector()

# More sensitive (catches more, may have false positives)
detector.size_threshold = 0.8  # Default: 0.7
detector.baseline_threshold = 0.15  # Default: 0.20

# Less sensitive (catches less, fewer false positives)
detector.size_threshold = 0.6
detector.baseline_threshold = 0.25
```

---

## TROUBLESHOOTING

### Issue: No super/subscripts detected
**Check:**
1. Does PDF have font information? (Try analyzing manually)
2. Are super/subscripts in different font size?
3. Try adjusting thresholds

### Issue: Too many false positives
**Solution:**
- Increase size_threshold (0.7 → 0.6)
- Increase baseline_threshold (0.20 → 0.25)

### Issue: Missing obvious super/subscripts
**Solution:**
- Decrease size_threshold (0.7 → 0.8)
- Decrease baseline_threshold (0.20 → 0.15)
- Check if PDF has size/baseline info

---

## INTEGRATION CHECKLIST

- [ ] superscript_detector.py imported successfully
- [ ] SuperscriptSubscriptDetector creates correctly
- [ ] analyze_page() runs without errors
- [ ] Statistics print correctly
- [ ] Superscripts detected on test page
- [ ] Subscripts detected on test page
- [ ] Formulas found correctly
- [ ] Integration with extractor planned
- [ ] Test on real PDF with formulas
- [ ] Verify detected scripts are preserved in output

---

## NEXT STEPS

After Phase 1 is tested:

**Phase 6: Footnote System** (8 hours)
- Extract footnote definitions at page bottom
- Match markers (*1) with definitions
- Preserve complete footnote structure

---

## SUMMARY

✅ **Created:**
- superscript_detector.py (complete module)

✅ **Features:**
- Font size analysis
- Baseline offset detection
- Pattern matching
- Context awareness
- Formula finding
- Statistics reporting

✅ **Detects:**
- Chemical formulas (H₂O, CO₂)
- Math expressions (x², y³)
- Footnote markers (*1, *2)
- Unicode super/subscripts
- Reference numbers

⏱ **Time to Test:**
- Quick test: 5 minutes
- Full integration: 4-6 hours

---

**Ready to test Phase 1?**

Run the 5-minute test and let me know the results!
