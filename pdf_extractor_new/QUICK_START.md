# 🚀 QUICK START - Get Running in 2 Minutes!

## ⚡ **FASTEST METHOD (Windows)**

1. **Double-click:** `START_API.bat`
2. **Wait** for "Uvicorn running on..."
3. **Open:** `web_ui.html` in your browser
4. **Upload** a PDF and extract!

**Done!** ✅

---

## 📋 **STEP-BY-STEP (All Platforms)**

### **Step 1: Install Dependencies** (First time only)

```bash
cd D:\pdf_extractor_new
pip install -r requirements.txt
```

Wait for installation to complete (~30 seconds)

---

### **Step 2: Start the API Server**

```bash
python start_api.py
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
🚀 PDF Extractor API Started
📖 Docs: http://localhost:8000/docs
```

**✅ Server is running!** Keep this terminal open.

---

### **Step 3: Use It**

**Option A: Web Interface (Easiest)**
1. Open `web_ui.html` in your browser
2. Drag & drop a PDF
3. Click "Extract Text"
4. Get results!

**Option B: API Documentation**
1. Go to: http://localhost:8000/docs
2. Try the "/extract" endpoint
3. Upload a PDF
4. See results

**Option C: Command Line**
```bash
# In a NEW terminal (keep API running)
python main.py -f your_document.pdf
```

---

## 🎯 **WHAT EACH FILE DOES**

| File | Purpose | When to Use |
|------|---------|-------------|
| `START_API.bat` | Start server (Windows) | Click to start everything |
| `start_api.py` | Start server (all platforms) | `python start_api.py` |
| `web_ui.html` | Web interface | Open in browser after API starts |
| `main.py` | Command-line tool | Batch processing PDFs |
| `api.py` | API server code | (Auto-loaded by start_api.py) |

---

## ✅ **VERIFY IT'S WORKING**

### **Check 1: API Health**
Open in browser: http://localhost:8000/health

Should see:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-06...",
  "extractor": "ready"
}
```

### **Check 2: Web UI Connection**
Open `web_ui.html`

Should see:
- Green dot ✅
- "Connected to API"

### **Check 3: Upload a Test PDF**
1. Use web UI or API docs
2. Upload any PDF
3. Should get extracted text back

---

## 🔧 **IF SOMETHING GOES WRONG**

### **Problem: "python is not recognized"**
**Fix:** Install Python from python.org

### **Problem: "pip install fails"**
**Fix:** 
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### **Problem: "Port 8000 already in use"**
**Fix:** Change port in `start_api.py` to 8001

### **Problem: Web UI shows "Not Found"**
**Fix:** Make sure API server is running first!

**More help:** See `TROUBLESHOOTING.md`

---

## 📚 **NEXT STEPS**

### **Basic Usage:**
```bash
# Process single file
python main.py -f document.pdf

# Process entire folder
python main.py

# Results appear in output/ folder
```

### **API Usage:**
```bash
# Upload via API
curl -X POST "http://localhost:8000/extract" -F "file=@document.pdf"

# Check job status
curl http://localhost:8000/stats
```

### **Python Integration:**
```python
from extractor import JapanesePDFExtractor

extractor = JapanesePDFExtractor()
text = extractor.extract_pdf('document.pdf')
print(text)
```

---

## 🎯 **COMMON WORKFLOWS**

### **Workflow 1: Single Document (Web UI)**
1. Start API: `START_API.bat`
2. Open: `web_ui.html`
3. Upload PDF
4. Download result

### **Workflow 2: Batch Processing (Command Line)**
1. Put PDFs in `input/` folder
2. Run: `python main.py`
3. Get results in `output/` folder
4. Check logs in `logs/` folder

### **Workflow 3: API Integration (Your App)**
1. Start API: `python start_api.py`
2. Send POST to: `http://localhost:8000/extract`
3. Get JSON response with text
4. Process in your application

---

## 📊 **PERFORMANCE EXPECTATIONS**

| PDF Size | Pages | Processing Time |
|----------|-------|----------------|
| Small | 1-10 | 2-10 seconds |
| Medium | 10-50 | 10-60 seconds |
| Large | 50-100 | 1-3 minutes |
| Very Large | 100+ | 3-10 minutes |

**Speed:** ~2 seconds per page on average

---

## 🎉 **YOU'RE READY!**

Start extracting Japanese PDFs with perfect reading order!

**Questions?** Check:
- `README.md` - Full documentation
- `API_DOCUMENTATION.md` - API reference
- `TROUBLESHOOTING.md` - Fix common issues
- http://localhost:8000/docs - Interactive API docs (when running)

**Happy extracting!** 🚀📄
