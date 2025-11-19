# 🔧 TROUBLESHOOTING GUIDE

## Problem: Web UI Shows "Not Found" or "Detail: Not Found"

### **Solution:**

The web UI requires the API server to be running. Here's how to fix it:

---

## ✅ **QUICK FIX (3 Steps)**

### **Step 1: Start the API Server**

**Option A: Double-click the batch file (Windows)**
```
Double-click: START_API.bat
```

**Option B: Use command line**
```bash
cd D:\pdf_extractor_new
python start_api.py
```

### **Step 2: Wait for Server to Start**

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
🚀 PDF Extractor API Started
📖 Docs: http://localhost:8000/docs
```

### **Step 3: Refresh the Web UI**

Open `web_ui.html` in your browser and refresh (F5)

The status should change from ❌ to ✅

---

## 🔍 **DETAILED TROUBLESHOOTING**

### **Issue 1: "python is not recognized"**

**Problem:** Python not installed or not in PATH

**Solution:**
1. Download Python from https://python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart terminal
4. Try again

---

### **Issue 2: "pip install fails"**

**Problem:** Dependencies can't install

**Solution:**
```bash
# Try upgrading pip first
python -m pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt
```

---

### **Issue 3: "Port 8000 already in use"**

**Problem:** Another application is using port 8000

**Solution A: Stop the other application**
```bash
# Windows - Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

**Solution B: Use a different port**
```bash
# Edit start_api.py, change line:
port=8000  # Change to 8001 or 8080

# Then update web_ui.html:
const API_URL = 'http://localhost:8001';  # Match your port
```

---

### **Issue 4: "CORS error" in browser console**

**Problem:** Browser blocking requests

**Solution:** The API has CORS enabled, but if you still see this:

1. Make sure API server is actually running
2. Check browser console for actual error
3. Try accessing http://localhost:8000/health directly
4. Clear browser cache

---

### **Issue 5: Web UI loads but file upload fails**

**Check these:**

1. **File size** - Max 50MB by default
2. **File type** - Must be .pdf
3. **API running** - Check status indicator
4. **Browser console** - Press F12, check for errors

---

## 🚀 **ALTERNATIVE: Use Without Web UI**

If web UI isn't working, use the command line:

### **Single File:**
```bash
python main.py -f your_document.pdf
```

### **Batch Processing:**
```bash
# Put PDFs in input/ folder, then:
python main.py
```

### **Python Script:**
```python
from extractor import JapanesePDFExtractor

extractor = JapanesePDFExtractor()
text = extractor.extract_pdf('document.pdf')
print(text)
```

---

## 📝 **TESTING CHECKLIST**

Run these commands to test your setup:

```bash
# 1. Check Python
python --version
# Should show: Python 3.7+ 

# 2. Check dependencies
pip list | findstr pdfplumber
pip list | findstr fastapi
pip list | findstr uvicorn
# Should show installed versions

# 3. Test extractor directly
python -c "from extractor import JapanesePDFExtractor; print('OK')"
# Should print: OK

# 4. Test API
python start_api.py
# Should start server

# 5. In another terminal, test API
curl http://localhost:8000/health
# Should return JSON with "status": "healthy"
```

---

## 🆘 **STILL NOT WORKING?**

### **Get Detailed Error Info:**

```bash
# Run with debug mode
python start_api.py --log-level debug

# Or check logs
cd D:\pdf_extractor_new\logs
type processing_*.log
```

### **Common Error Messages:**

| Error | Cause | Fix |
|-------|-------|-----|
| "No module named 'pdfplumber'" | Not installed | `pip install pdfplumber` |
| "Address already in use" | Port 8000 taken | Change port or kill process |
| "Permission denied" | Admin rights needed | Run as Administrator |
| "File not found" | Wrong directory | Check you're in D:\pdf_extractor_new |

---

## 🎯 **QUICK START (FROM SCRATCH)**

If nothing works, start fresh:

```bash
# 1. Navigate to folder
cd D:\pdf_extractor_new

# 2. Clean install
pip uninstall pdfplumber fastapi uvicorn -y
pip install -r requirements.txt

# 3. Test extraction without API
python -c "from extractor import JapanesePDFExtractor; e = JapanesePDFExtractor(); print('Extractor: OK')"

# 4. Start API
python start_api.py

# 5. Open browser
# Go to: http://localhost:8000/docs

# 6. Try web UI
# Open: web_ui.html
```

---

## 📞 **NEED MORE HELP?**

1. Check the logs in `logs/` folder
2. Try the command-line interface instead: `python main.py`
3. Test with a simple PDF first
4. Make sure your PDF isn't password-protected

---

## ✅ **SUCCESS INDICATORS**

You know it's working when:

✓ API server shows "Uvicorn running"
✓ Web UI status shows green dot with "Connected"
✓ http://localhost:8000/health returns JSON
✓ http://localhost:8000/docs loads Swagger UI
✓ Can upload and extract a PDF

---

## 🔧 **DEVELOPER MODE**

For development and debugging:

```bash
# Run with auto-reload
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
uvicorn api:app --log-level debug

# Test API with curl
curl -X POST "http://localhost:8000/extract" -F "file=@test.pdf"
```

---

**Remember:** The web UI is just a convenience interface. The core extraction works perfectly via command line even if the web UI has issues!
