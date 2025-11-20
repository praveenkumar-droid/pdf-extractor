# OCR Guide - Extracting Text from Scanned PDFs

## Overview

The PDF Extractor now supports **Optical Character Recognition (OCR)** for scanned PDFs that don't have text layers. This feature automatically detects image-based pages and extracts text using advanced OCR engines.

## Features

✅ **Automatic Detection** - Detects scanned pages automatically (pages with < 10 words)
✅ **Japanese + English Support** - Optimized for Japanese pharmaceutical documents
✅ **High Accuracy** - Uses EasyOCR with deep learning models
✅ **Seamless Integration** - Works transparently with existing extraction pipeline
✅ **GPU Acceleration** - Optional GPU support for faster processing
✅ **Confidence Scoring** - Only uses OCR results above confidence threshold
✅ **Hybrid Documents** - Handles mixed text-based and scanned pages in same PDF

---

## Quick Start

### 1. Install OCR Engine

**Option A: EasyOCR (Recommended for Japanese)**
```bash
pip install easyocr
```

**Option B: Tesseract OCR (Alternative)**
```bash
# Install Python package
pip install pytesseract

# Install Tesseract binary:
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-jpn

# macOS:
brew install tesseract tesseract-lang

# Windows:
# Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Enable OCR in config.py

```python
# Enable OCR extraction
ENABLE_OCR_EXTRACTION = True

# Configure OCR settings
OCR_ENGINE = "auto"              # auto-select best available
OCR_LANGUAGES = ['ja', 'en']     # Japanese + English
OCR_MIN_CONFIDENCE = 0.5         # Minimum confidence (0.0-1.0)
OCR_MIN_WORDS_THRESHOLD = 10     # Pages with < 10 words trigger OCR
```

### 3. Run Extraction

```bash
# Web UI (automatic OCR for scanned pages)
python api.py
# Visit http://localhost:8000/ui

# Command line
python run_complete_system.py input/scanned_document.pdf
```

---

## Configuration Options

### Core Settings (config.py)

```python
# ═══════════════════════════════════════════════════════════════
# OCR SETTINGS
# ═══════════════════════════════════════════════════════════════

# Enable/disable OCR
ENABLE_OCR_EXTRACTION = True        # Set to False to disable OCR

# OCR engine selection
OCR_ENGINE = "auto"                 # Options: "auto", "easyocr", "tesseract"
                                    # "auto" - Auto-select best available
                                    # "easyocr" - Use EasyOCR (recommended)
                                    # "tesseract" - Use Tesseract OCR

# Languages to recognize
OCR_LANGUAGES = ['ja', 'en']        # ['ja'] for Japanese only
                                    # ['en'] for English only
                                    # ['ja', 'en'] for both (recommended)

# Performance settings
OCR_USE_GPU = False                 # Enable GPU acceleration (EasyOCR only)
                                    # Requires CUDA-capable GPU
                                    # 5-10x faster with GPU

OCR_RESOLUTION = 300                # DPI for image conversion
                                    # Higher = better quality, slower
                                    # 300 = good balance
                                    # 600 = maximum quality

# Quality thresholds
OCR_MIN_CONFIDENCE = 0.5            # Minimum confidence (0.0-1.0)
                                    # 0.5 = balanced (recommended)
                                    # 0.7 = high quality only
                                    # 0.3 = accept more low-confidence

OCR_MIN_WORDS_THRESHOLD = 10        # Trigger OCR if page has < N words
                                    # 10 = default (good for most cases)
                                    # 5 = more aggressive OCR
                                    # 20 = conservative OCR

# Debug settings
OCR_VERBOSE = False                 # Print OCR progress and confidence
                                    # True = show detailed OCR output
                                    # False = silent operation
```

---

## Usage Examples

### Example 1: Basic OCR with EasyOCR

```python
from ocr_processor import OCRProcessor

# Initialize OCR
processor = OCRProcessor(
    languages=['ja', 'en'],
    engine='easyocr',
    verbose=True
)

# Process single page
with pdfplumber.open('scanned.pdf') as pdf:
    page = pdf.pages[0]
    result = processor.process_page(page)

    if result.success:
        print(f"Extracted: {result.text}")
        print(f"Confidence: {result.confidence:.1%}")
    else:
        print(f"Failed: {result.error}")
```

### Example 2: Automatic OCR Detection

```python
from ocr_processor import extract_with_ocr

# Automatically detect and OCR scanned pages
text = extract_with_ocr(
    'mixed_document.pdf',  # Can have both text and scanned pages
    languages=['ja', 'en'],
    verbose=True
)

print(text)
```

### Example 3: Process Multiple Scanned Pages

```python
processor = OCRProcessor(languages=['ja', 'en'])

# Process specific pages
scanned_pages = [1, 3, 5, 7]  # Page numbers
results = processor.process_pdf('document.pdf', scanned_pages)

for page_num, result in results.items():
    print(f"Page {page_num}:")
    print(f"  Confidence: {result.confidence:.1%}")
    print(f"  Characters: {result.char_count}")
```

---

## Performance Optimization

### GPU Acceleration (EasyOCR)

**5-10x faster** with CUDA-capable GPU:

```python
# config.py
OCR_USE_GPU = True
```

**Requirements:**
- NVIDIA GPU with CUDA support
- CUDA Toolkit installed
- PyTorch with CUDA

**Installation:**
```bash
# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install EasyOCR
pip install easyocr
```

### Resolution vs Speed

| Resolution | Quality | Speed | Use Case |
|------------|---------|-------|----------|
| 150 DPI | Low | Fast | Quick preview |
| 300 DPI | Good | Medium | **Recommended** |
| 600 DPI | Excellent | Slow | High quality docs |

```python
# config.py
OCR_RESOLUTION = 300  # Balanced (default)
```

### Batch Processing

Process multiple PDFs efficiently:

```bash
# Process entire folder with OCR
python run_complete_system.py input/

# Web API batch endpoint
curl -X POST http://localhost:8000/extract/batch \
  -F "files=@scan1.pdf" \
  -F "files=@scan2.pdf" \
  -F "files=@scan3.pdf"
```

---

## Quality & Troubleshooting

### High Confidence Results

```python
# Require high confidence for OCR
OCR_MIN_CONFIDENCE = 0.7  # 70% minimum

# Increase resolution for better quality
OCR_RESOLUTION = 600
```

### Low Quality Scans

```python
# Accept lower confidence for poor quality scans
OCR_MIN_CONFIDENCE = 0.3  # 30% minimum

# Enable denoising (future feature)
OCR_DENOISE = True
```

### Debug OCR Issues

```python
# Enable verbose output
OCR_VERBOSE = True

# Run OCR directly
python ocr_processor.py input/scanned.pdf
```

### Common Issues

**Issue:** OCR not triggering
- **Cause:** Page has > 10 words (not detected as scanned)
- **Solution:** Reduce `OCR_MIN_WORDS_THRESHOLD = 5`

**Issue:** Low quality extraction
- **Cause:** Poor scan quality or low resolution
- **Solution:** Increase `OCR_RESOLUTION = 600`

**Issue:** Slow processing
- **Cause:** CPU-only processing
- **Solution:** Enable `OCR_USE_GPU = True` (requires GPU)

**Issue:** Wrong language detected
- **Cause:** Language not in OCR_LANGUAGES
- **Solution:** Add language: `OCR_LANGUAGES = ['ja', 'en', 'zh']`

---

## OCR Engines Comparison

### EasyOCR (Recommended)

✅ **Pros:**
- Excellent Japanese support
- No external dependencies
- Easy installation
- GPU acceleration support
- Pre-trained models
- High accuracy

❌ **Cons:**
- Large download (models ~100MB per language)
- Slower on CPU
- Requires more RAM

**Installation:**
```bash
pip install easyocr
```

### Tesseract OCR (Alternative)

✅ **Pros:**
- Lightweight
- Fast on CPU
- Wide language support
- Mature and stable

❌ **Cons:**
- Requires binary installation
- Lower accuracy for Japanese
- No GPU support
- More setup required

**Installation:**
```bash
pip install pytesseract
# Plus system installation of Tesseract
```

---

## API Integration

### Web UI

OCR works automatically:
1. Upload PDF at `http://localhost:8000/ui`
2. System detects scanned pages
3. OCR applied automatically
4. Results shown with confidence scores

### REST API

```bash
# Extract with automatic OCR
curl -X POST http://localhost:8000/extract \
  -F "file=@scanned_document.pdf"

# Response includes OCR metadata
{
  "success": true,
  "text": "...",
  "features_used": {
    "ocr_extraction": true
  },
  "ocr_pages": [1, 3, 5],
  "ocr_confidence": 0.87
}
```

---

## Best Practices

### 1. Pre-process Scans
- Scan at 300+ DPI
- Use black & white for text documents
- Ensure good lighting/contrast
- Remove shadows and skew

### 2. Configure Appropriately
- Start with defaults
- Adjust confidence based on results
- Enable GPU if available
- Use 300 DPI for most cases

### 3. Validate Results
- Check confidence scores
- Review OCR output
- Compare with manual inspection
- Adjust thresholds as needed

### 4. Hybrid Documents
- System handles mixed PDFs automatically
- Text-based pages → Regular extraction
- Scanned pages → OCR extraction
- No configuration needed

---

## Testing OCR

### Test with Sample Document

```bash
# Test OCR directly
cd pdf_extractor_new
python ocr_processor.py ../input/scanned_sample.pdf
```

### Check OCR Status

```python
from ocr_processor import OCRProcessor

processor = OCRProcessor()
if processor.is_available():
    print(f"✅ OCR ready: {processor.engine_used}")
else:
    print("❌ OCR not available - install easyocr or pytesseract")
```

---

## FAQ

**Q: Does OCR slow down regular PDFs?**
A: No. OCR only runs on pages with < 10 words (scanned pages). Text-based pages use regular extraction.

**Q: Can I use OCR for all pages?**
A: Yes, set `OCR_MIN_WORDS_THRESHOLD = 999999` to force OCR on all pages (not recommended).

**Q: Which engine is better?**
A: EasyOCR for Japanese documents. Tesseract for English-only or if you need lightweight.

**Q: Does OCR work offline?**
A: Yes. Both engines work completely offline after initial model download.

**Q: How accurate is OCR?**
A: EasyOCR achieves 85-95% accuracy on good quality Japanese scans. Results vary by scan quality.

**Q: Can I train custom models?**
A: EasyOCR supports custom models. See EasyOCR documentation for details.

---

## Performance Benchmarks

### EasyOCR (CPU)
- **Speed:** ~5-10 seconds per page
- **Accuracy:** 85-95% (Japanese)
- **Memory:** ~2GB RAM

### EasyOCR (GPU)
- **Speed:** ~0.5-1 second per page (10x faster)
- **Accuracy:** Same as CPU
- **Memory:** ~4GB VRAM

### Tesseract
- **Speed:** ~2-3 seconds per page
- **Accuracy:** 70-80% (Japanese)
- **Memory:** ~500MB RAM

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review OCR logs (enable `OCR_VERBOSE = True`)
- Test with `python ocr_processor.py <pdf_path>`
- Report issues with sample PDF and logs

---

**Last Updated:** 2025-11-20
**OCR Version:** 1.0
**Status:** ✅ Production Ready
