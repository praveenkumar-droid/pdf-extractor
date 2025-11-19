# Place your PDF files here

This folder is watched by the extraction system.

## Quick Start

1. **Copy your PDF files** into this folder
2. **Run the extractor**: `python main.py`
3. **Get results** from the `output/` folder

## Folder Structure

You can organize PDFs in subdirectories:

```
input/
├── medical/
│   ├── drug_info_1.pdf
│   └── drug_info_2.pdf
├── legal/
│   └── contract.pdf
└── research/
    └── paper.pdf
```

The output folder will mirror this structure (by default).

## Supported Files

- ✅ `.pdf` files
- ✅ Japanese text PDFs
- ✅ Multi-page documents
- ✅ Multi-column layouts

## Not Supported

- ❌ Scanned PDFs (OCR needed first)
- ❌ Password-protected PDFs
- ❌ Image-only PDFs
- ❌ Corrupted files
