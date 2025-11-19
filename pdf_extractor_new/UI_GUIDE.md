# 🎨 COMPLETE UI GUIDE - ALL 3 OPTIONS

This document shows you **3 different ways** to use the PDF Extractor with a User Interface.

---

## 🚀 QUICK START (Choose One)

### ⚡ **FASTEST WAY (Windows)**

1. **Double-click:** `START_HERE.bat`
2. **Open browser:** http://localhost:8000/ui
3. **Done!** 🎉

### 💻 **COMMAND LINE WAY**

```bash
cd D:\pdf_extractor_new
pip install -r requirements.txt
python start_api.py
```

Then open: http://localhost:8000/ui

---

## 🎨 **OPTION 1: Web UI (Recommended)**

### **Best For:** 
- Non-technical users
- Quick uploads
- Visual interface
- Drag & drop

### **How to Access:**

1. **Start the server:**
   ```bash
   python start_api.py
   ```

2. **Open browser:**
   ```
   http://localhost:8000/ui
   ```

3. **Or open directly:**
   ```
   Double-click: web_ui.html
   ```

### **Features:**

✅ **Drag & Drop** - Drop PDF files directly  
✅ **Live Statistics** - See character/line/word counts  
✅ **Text Preview** - View extracted text immediately  
✅ **Extraction Options:**
   - Normalize characters (半角→全角)
   - Fix spacing (Japanese/English)
   - Remove headers/footers

✅ **Beautiful Design** - Modern gradient UI  
✅ **No Installation** - Just works in browser  

### **Screenshots:**

```
┌─────────────────────────────────────────┐
│  📄 Japanese PDF Text Extractor        │
│  Upload your PDF and get clean text    │
├─────────────────────────────────────────┤
│                                         │
│   ┌─────────────────────────────┐      │
│   │         📁                  │      │
│   │  Drop PDF file here         │      │
│   │  or click to browse         │      │
│   └─────────────────────────────┘      │
│                                         │
│   ☑ Normalize characters               │
│   ☑ Fix spacing                        │
│   ☑ Remove headers/footers             │
│                                         │
│   [ Extract Text ]                     │
│                                         │
│   Results:                             │
│   📊 5,420 characters                  │
│   📊 234 lines                         │
│   📊 1,823 words                       │
│                                         │
│   Preview:                             │
│   第1章 序論                           │
│   本文...                              │
└─────────────────────────────────────────┘
```

---

## 📖 **OPTION 2: Swagger UI (Interactive API Docs)**

### **Best For:**
- Developers
- API testing
- All endpoint access
- Technical users

### **How to Access:**

1. **Start the server:**
   ```bash
   python start_api.py
   ```

2. **Open browser:**
   ```
   http://localhost:8000/docs
   ```

### **Features:**

✅ **Interactive Testing** - Try all endpoints  
✅ **9 API Endpoints:**
   - POST /extract - Single file upload
   - POST /extract/batch - Multiple files
   - GET /jobs/{job_id} - Job status
   - GET /files/list - List extracted files
   - GET /stats - System statistics
   - GET /health - Health check
   - GET /download/{filename} - Download results
   - GET /logs/list - View logs
   - GET /logs/{filename} - Get log content

✅ **Auto-Generated** - Always up to date  
✅ **Request Examples** - See how to call API  
✅ **Response Examples** - See expected outputs  

### **How to Use:**

```
1. Find the endpoint you want (e.g., POST /extract)
2. Click on it to expand
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See response below!
```

### **Example: Upload a PDF**

```
1. Go to: http://localhost:8000/docs
2. Click: POST /extract
3. Click: "Try it out"
4. Click: "Choose File" and select your PDF
5. Set options:
   - normalize: true
   - fix_spacing: true
   - remove_headers: true
6. Click: "Execute"
7. See extracted text in response!
```

---

## 📚 **OPTION 3: ReDoc (Clean Documentation)**

### **Best For:**
- Reading documentation
- Understanding API structure
- Sharing with team
- Clean, professional look

### **How to Access:**

1. **Start the server:**
   ```bash
   python start_api.py
   ```

2. **Open browser:**
   ```
   http://localhost:8000/redoc
   ```

### **Features:**

✅ **Beautiful Layout** - Easy to read  
✅ **Complete Documentation** - All endpoints explained  
✅ **Request/Response Examples** - See formats  
✅ **Search Functionality** - Find endpoints quickly  
✅ **Downloadable** - Can export as PDF  

### **Less Interactive** - Better for reading than testing

---

## 🔄 **COMPARISON TABLE**

| Feature | Web UI | Swagger UI | ReDoc |
|---------|---------|-----------|--------|
| **Easy for non-tech** | ✅ Best | ⚠️ Medium | ⚠️ Medium |
| **Drag & drop** | ✅ Yes | ❌ No | ❌ No |
| **API testing** | ⚠️ Limited | ✅ Best | ❌ No |
| **All endpoints** | ❌ No | ✅ Yes | ✅ Yes |
| **Beautiful design** | ✅ Yes | ⚠️ OK | ✅ Yes |
| **Documentation** | ❌ No | ✅ Yes | ✅ Best |
| **Quick uploads** | ✅ Best | ⚠️ OK | ❌ No |

---

## 🎯 **WHICH ONE SHOULD YOU USE?**

### **For End Users (Non-Technical):**
```
✅ Use: Web UI (http://localhost:8000/ui)

Why:
- Beautiful interface
- Easy drag & drop
- No technical knowledge needed
- Instant results
```

### **For Developers:**
```
✅ Use: Swagger UI (http://localhost:8000/docs)

Why:
- Test all API endpoints
- See request/response formats
- Interactive API exploration
- Development & debugging
```

### **For Documentation:**
```
✅ Use: ReDoc (http://localhost:8000/redoc)

Why:
- Clean, professional look
- Easy to read
- Share with team
- Print/export friendly
```

---

## 🚀 **COMPLETE STARTUP GUIDE**

### **Step 1: First Time Setup (2 minutes)**

```bash
# 1. Open terminal/command prompt
cd D:\pdf_extractor_new

# 2. Install dependencies (first time only)
pip install -r requirements.txt
```

### **Step 2: Start the Server**

**Option A: Windows - Double Click**
```
📁 D:\pdf_extractor_new\
   └─ 📄 START_HERE.bat  ← Double-click!
```

**Option B: Command Line**
```bash
python start_api.py
```

### **Step 3: Open Your Favorite UI**

You'll see this output:
```
============================================================
🚀 PDF Extractor API Started
============================================================
🎨 Web UI:  http://localhost:8000/ui
📖 API Docs: http://localhost:8000/docs
📚 ReDoc:    http://localhost:8000/redoc
============================================================
```

**Click on any link!**

---

## 💡 **TIPS & TRICKS**

### **Web UI Tips:**

1. **Drag & Drop Multiple Times**
   - Extract one PDF
   - Drag another immediately
   - No need to refresh!

2. **Copy Text Easily**
   - Results show in text preview
   - Click inside, Ctrl+A, Ctrl+C
   - Paste anywhere!

3. **Change Options**
   - Toggle checkboxes before extracting
   - Each PDF can use different options

### **Swagger UI Tips:**

1. **Save API Key** (if authentication added)
   - Click "Authorize" button
   - Enter API key once
   - Works for all requests

2. **Download Response**
   - After execution, click "Download"
   - Saves JSON response
   - Great for testing

3. **Copy as cURL**
   - See the cURL command
   - Use in terminal/scripts
   - Easy automation

---

## 🔧 **TROUBLESHOOTING**

### **Problem: Can't Access UI**

```
Error: Connection refused
```

**Solution:**
```bash
# Check if server is running
python start_api.py

# Make sure you see:
# "Uvicorn running on http://0.0.0.0:8000"
```

### **Problem: CORS Error in Web UI**

```
Error: CORS policy blocked
```

**Solution:**
Already configured! CORS is enabled in api.py.
If still having issues, check browser console.

### **Problem: Port Already in Use**

```
Error: Address already in use
```

**Solution:**
```bash
# Option 1: Kill existing process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Option 2: Use different port
uvicorn api:app --port 8001
```

### **Problem: File Upload Fails**

```
Error: 413 Request Entity Too Large
```

**Solution:**
File is too large (>50MB default).
Increase limit in api.py:
```python
app.add_middleware(
    ...,
    max_upload_size=100 * 1024 * 1024  # 100MB
)
```

---

## 🌐 **ACCESSING FROM OTHER DEVICES**

### **Same Network (Phone, Tablet, Other Computer)**

1. **Find your IP address:**
   ```bash
   # Windows
   ipconfig
   # Look for: IPv4 Address (e.g., 192.168.1.100)
   
   # Mac/Linux
   ifconfig
   ```

2. **Start server on all interfaces:**
   ```bash
   # Already configured! Server binds to 0.0.0.0
   python start_api.py
   ```

3. **Access from other device:**
   ```
   http://192.168.1.100:8000/ui
   (Replace with your IP)
   ```

---

## 🎨 **CUSTOMIZING THE WEB UI**

### **Change Colors:**

Edit `web_ui.html`:
```css
/* Find this line: */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your colors: */
background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
```

### **Change Title:**

Edit `web_ui.html`:
```html
<!-- Find: -->
<h1>📄 Japanese PDF Text Extractor</h1>

<!-- Change to: -->
<h1>🏥 Medical Document Processor</h1>
```

### **Add Logo:**

Edit `web_ui.html`:
```html
<!-- Add before <h1>: -->
<img src="your-logo.png" alt="Logo" style="width: 100px;">
```

---

## 📱 **MOBILE ACCESS**

The Web UI is **mobile-responsive**!

1. **Start server on your computer**
2. **Find your computer's IP** (see above)
3. **Open on phone:**
   ```
   http://192.168.1.100:8000/ui
   ```

4. **Upload PDFs from phone**
5. **View results immediately**

Works on:
- ✅ iPhone Safari
- ✅ Android Chrome
- ✅ iPad Safari
- ✅ Any modern mobile browser

---

## 🎯 **QUICK REFERENCE**

### **URLs (After starting server):**

```
Main Web UI:        http://localhost:8000/ui
API Documentation:  http://localhost:8000/docs
Alternative Docs:   http://localhost:8000/redoc
Health Check:       http://localhost:8000/health
System Stats:       http://localhost:8000/stats
```

### **Starting Server:**

```bash
# Easy way (Windows)
START_HERE.bat

# Command line
python start_api.py

# Custom port
uvicorn api:app --port 8080

# With auto-reload
uvicorn api:app --reload
```

### **Stopping Server:**

```bash
# Press: Ctrl+C in terminal
# Or close the command prompt window
```

---

## 📚 **NEXT STEPS**

1. ✅ **Try the Web UI** - http://localhost:8000/ui
2. ✅ **Upload a test PDF** - See it work
3. ✅ **Explore API docs** - http://localhost:8000/docs
4. ✅ **Share with team** - They can access from their computers
5. ✅ **Integrate into your app** - Use the API endpoints

---

## 🎉 **YOU'RE READY!**

**Just run:** `START_HERE.bat` or `python start_api.py`

**Then open:** http://localhost:8000/ui

**Start extracting PDFs with a beautiful UI!** 🚀

Need help? Check the other documentation files:
- README.md - Overview
- API_DOCUMENTATION.md - API reference
- GETTING_STARTED.md - Setup guide
