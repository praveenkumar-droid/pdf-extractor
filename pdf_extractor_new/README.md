# Japanese PDF Text Extractor

100% Deterministic PDF text extraction with perfect visual reading order for Japanese documents.

## Features

✅ **Perfect Reading Order** - Extracts text exactly as it appears visually on the page  
✅ **Multi-Column Support** - Automatically detects and handles multi-column layouts  
✅ **Header/Footer Removal** - Intelligently removes page numbers, headers, and footers  
✅ **Character Normalization** - Converts half-width to full-width for Japanese text  
✅ **Batch Processing** - Process entire folders of PDFs  
✅ **100% Deterministic** - Same input always produces same output  
✅ **Detailed Logging** - Complete logs and error reports  

---

## Quick Start

### Option A: Command Line Interface

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Place PDFs in Input Folder
```
pdf_extractor_new/
├── input/          ← Place your PDF files here
│   ├── doc1.pdf
│   ├── doc2.pdf
│   └── ...
```

#### 3. Run Extraction
```bash
python main.py
```

#### 4. Get Results
```
pdf_extractor_new/
├── output/         ← Extracted text files appear here
│   ├── doc1.txt
│   ├── doc2.txt
│   └── ...
└── logs/           ← Processing logs and reports
```

### Option B: REST API (FastAPI)

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Start API Server
```bash
python start_api.py
```

#### 3. Access API
- **Interactive Docs**: http://localhost:8000/docs
- **Web UI**: Open `web_ui.html` in browser
- **API Endpoint**: http://localhost:8000/extract

#### 4. Upload via API
```bash
curl -X POST "http://localhost:8000/extract" -F "file=@document.pdf"
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

---

## Usage Examples

### Basic Usage (Process all PDFs in input folder)
```bash
python main.py
```

### Process Specific Folder
```bash
python main.py -i "C:/my_pdfs" -o "C:/output"
```

### Process Single File
```bash
python main.py -f "document.pdf"
```

### Reprocess All Files (Don't Skip Existing)
```bash
python main.py --no-skip
```

### Flat Output Structure (No Subdirectories)
```bash
python main.py --flat
```

### Don't Search Subdirectories
```bash
python main.py --no-recursive
```

---

## Configuration

Edit `config.py` to customize extraction behavior:

```python
# Extraction settings
COLUMN_GAP_THRESHOLD = 50    # Gap size to detect columns
LINE_HEIGHT_THRESHOLD = 15   # Max Y-distance for same line

# Processing settings
SKIP_EXISTING = True         # Skip already processed files
RECURSIVE_SCAN = True        # Search subdirectories
PRESERVE_DIRECTORY_STRUCTURE = True  # Maintain folder structure

# Cleanup settings
REMOVE_HEADERS_FOOTERS = True
REMOVE_PAGE_NUMBERS = True
FIX_SPACING = True
JOIN_LINES = True
```

---

## How It Works

### Phase 1: Coordinate-Based Extraction
1. Extract all text elements with their X,Y coordinates
2. Detect page layout (single column, multi-column, etc.)
3. Detect repeating headers/footers across pages
4. Sort text by visual position (top→bottom, left→right)

### Phase 2: Rule-Based Cleanup
1. Remove headers, footers, page numbers
2. Normalize characters (half-width → full-width)
3. Fix spacing between Japanese and English
4. Join lines intelligently
5. Fix punctuation issues

**Result: 100% consistent, deterministic extraction**

---

## Output

### Text Files
- One `.txt` file per `.pdf` file
- UTF-8 encoding
- Clean, ready-to-use text

### Log Files
- `processing_YYYYMMDD_HHMMSS.log` - Detailed processing log
- `report_YYYYMMDD_HHMMSS.json` - Statistics and failed files

### Example Report
```json
{
  "timestamp": "20241106_143022",
  "statistics": {
    "total_files": 100,
    "successful": 98,
    "failed": 2,
    "success_rate": "98.0%"
  },
  "failed_files": [
    {"file": "corrupted.pdf", "error": "File is encrypted"}
  ]
}
```

---

## Programmatic Usage

```python
from processor import FileSystemProcessor

# Batch processing
processor = FileSystemProcessor(
    input_dir="my_pdfs",
    output_dir="extracted_text"
)
stats = processor.process_all()

# Single file
output_path = processor.process_file("document.pdf")
print(f"Extracted to: {output_path}")
```

---

## Troubleshooting

### No PDFs Found
- Make sure PDFs are in the `input/` folder
- Check if `RECURSIVE_SCAN = True` in config.py

### Extraction Quality Issues
- Adjust `COLUMN_GAP_THRESHOLD` in config.py (increase for wider columns)
- Adjust `LINE_HEIGHT_THRESHOLD` (increase for larger fonts)

### Encrypted PDFs
- Remove password protection before processing
- Use: `qpdf --decrypt input.pdf output.pdf`

### Performance
- Processing speed: ~1-5 seconds per page
- Large PDFs (100+ pages): ~2-10 minutes

---

## Requirements

- Python 3.7+
- pdfplumber 0.11.0+
- tqdm 4.66.1+

---

## Architecture

```
extractor.py     → Core extraction logic (coordinate-based)
processor.py     → Filesystem batch processor
main.py          → Command-line interface
config.py        → Configuration settings
```

---

## License

MIT License - Free to use for any purpose

---

## Support

For issues or questions:
1. Check logs in `logs/` folder
2. Review `report_*.json` for failed files
3. Adjust settings in `config.py`

---

## Why This Approach?

**Traditional PDF extraction** (e.g., `pypdf.extract_text()`):
- ❌ Extracts in PDF internal order (not visual order)
- ❌ Mixes columns randomly
- ❌ Inconsistent results

**Our coordinate-based approach**:
- ✅ Extracts in visual reading order
- ✅ Handles multi-column layouts
- ✅ 100% consistent and deterministic
- ✅ No AI needed = Free and fast

---

## Example Results

**Input PDF:**
```
┌─────────────┬─────────────┐
│ 第1章       │ 第2章       │
│ 序論        │ 本論        │
│ ...         │ ...         │
└─────────────┴─────────────┘
```

**Output Text:**
```
第1章
序論
...

第2章
本論
...
```

Perfect order, every time! ✨
