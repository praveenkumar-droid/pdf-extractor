# 📚 PDF Extractor API Documentation

Complete REST API for Japanese PDF text extraction with FastAPI.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
```bash
python start_api.py
```

Or directly with uvicorn:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access API
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Web UI**: Open `web_ui.html` in browser

---

## 📡 API Endpoints

### **Root**
```
GET /
```
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "Japanese PDF Text Extractor API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### **Health Check**
```
GET /health
```
Check if API is running and ready.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-06T14:30:22",
  "extractor": "ready"
}
```

---

### **Extract Single PDF**
```
POST /extract
```
Upload and extract text from a single PDF file.

**Parameters:**
- `file` (FormData): PDF file to upload (required)
- `normalize` (Query, boolean): Normalize characters (default: true)
- `fix_spacing` (Query, boolean): Fix spacing (default: true)
- `remove_headers` (Query, boolean): Remove headers/footers (default: true)

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@document.pdf"
```

**Example (Python):**
```python
import requests

with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8000/extract', files=files)
    result = response.json()
    print(result['text'])
```

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "text": "第1章\n序論\n...",
  "statistics": {
    "characters": 5420,
    "lines": 234,
    "words": 1823
  },
  "extracted_at": "2024-11-06T14:30:22"
}
```

---

### **Extract Batch PDFs**
```
POST /extract/batch
```
Upload multiple PDF files for batch processing.

**Parameters:**
- `files` (FormData): List of PDF files (max 10 files)

**Example (Python):**
```python
import requests

files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.pdf', 'rb')),
    ('files', open('doc3.pdf', 'rb'))
]

response = requests.post('http://localhost:8000/extract/batch', files=files)
job_id = response.json()['job_id']
print(f"Job ID: {job_id}")
```

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_files": 3,
  "message": "Batch processing started",
  "check_status": "/jobs/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### **Get Job Status**
```
GET /jobs/{job_id}
```
Check status of a batch processing job.

**Example:**
```bash
curl http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

**Response (In Progress):**
```json
{
  "status": "processing",
  "total": 3,
  "completed": 1,
  "failed": 0,
  "started_at": "2024-11-06T14:30:22"
}
```

**Response (Completed):**
```json
{
  "status": "completed",
  "total": 3,
  "completed": 3,
  "failed": 0,
  "results": [
    {
      "filename": "doc1.pdf",
      "success": true,
      "text": "...",
      "characters": 5420
    },
    {
      "filename": "doc2.pdf",
      "success": true,
      "text": "...",
      "characters": 3210
    }
  ],
  "completed_at": "2024-11-06T14:32:10"
}
```

---

### **Extract from Folder**
```
POST /extract/folder
```
Process all PDFs in the configured input folder.

**Parameters:**
- `input_path` (Query, optional): Custom input folder path

**Example:**
```bash
curl -X POST "http://localhost:8000/extract/folder"
```

**Response:**
```json
{
  "success": true,
  "job_id": "660e8400-e29b-41d4-a716-446655440000",
  "message": "Folder processing started",
  "check_status": "/jobs/660e8400-e29b-41d4-a716-446655440000"
}
```

---

### **List Extracted Files**
```
GET /files/list
```
List all extracted text files.

**Response:**
```json
{
  "total": 15,
  "files": [
    {
      "filename": "document",
      "path": "document.txt",
      "size": 54208,
      "modified": "2024-11-06T14:30:22"
    }
  ]
}
```

---

### **Download Extracted File**
```
GET /download/{filename}
```
Download an extracted text file.

**Example:**
```bash
curl -O http://localhost:8000/download/document
```

Returns the `.txt` file for download.

---

### **List Logs**
```
GET /logs/list
```
List all processing logs and reports.

**Response:**
```json
{
  "total": 5,
  "logs": [
    {
      "filename": "processing_20241106_143022.log",
      "type": "log",
      "size": 2048,
      "created": "2024-11-06T14:30:22"
    },
    {
      "filename": "report_20241106_143022.json",
      "type": "report",
      "size": 1024,
      "created": "2024-11-06T14:30:22"
    }
  ]
}
```

---

### **Get Log Content**
```
GET /logs/{filename}
```
View content of a log or report file.

**Example:**
```bash
curl http://localhost:8000/logs/report_20241106_143022.json
```

---

### **System Statistics**
```
GET /stats
```
Get overall system statistics.

**Response:**
```json
{
  "input_pdfs": 25,
  "output_texts": 23,
  "log_files": 5,
  "active_jobs": 1,
  "latest_report": {
    "statistics": {
      "total_files": 25,
      "successful": 23,
      "failed": 2
    }
  }
}
```

---

### **Delete Job**
```
DELETE /jobs/{job_id}
```
Remove a completed job from memory.

**Example:**
```bash
curl -X DELETE http://localhost:8000/jobs/550e8400-e29b-41d4-a716-446655440000
```

---

## 💻 Integration Examples

### **Node.js / Express**
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extractPDF(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    const response = await axios.post('http://localhost:8000/extract', form, {
        headers: form.getHeaders()
    });
    
    return response.data;
}

// Usage
extractPDF('document.pdf').then(result => {
    console.log('Extracted text:', result.text);
});
```

### **React / Next.js**
```javascript
async function uploadAndExtract(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch('http://localhost:8000/extract', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    return result;
}

// In component
const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    const result = await uploadAndExtract(file);
    console.log(result.text);
};
```

### **Python FastAPI Client**
```python
import requests

def extract_pdf(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:8000/extract', files=files)
        return response.json()['text']

# Usage
text = extract_pdf('document.pdf')
print(text)
```

---

## 🔒 Security Considerations

### **Production Deployment:**

1. **Add Authentication**
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/extract")
async def extract(
    file: UploadFile,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify token
    if credentials.credentials != "your-secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of code
```

2. **Configure CORS Properly**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

3. **Rate Limiting**
```bash
pip install slowapi
```

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/extract")
@limiter.limit("10/minute")
async def extract(request: Request, file: UploadFile):
    # ... code
```

4. **File Size Limits**
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@app.post("/extract")
async def extract(file: UploadFile):
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
```

---

## 🐳 Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t pdf-extractor-api .
docker run -p 8000:8000 pdf-extractor-api
```

---

## 📊 Performance

- **Single file extraction**: 1-5 seconds per page
- **Batch processing**: Processed in background, doesn't block API
- **Memory usage**: ~100-500MB depending on PDF size
- **Concurrent requests**: Supports multiple simultaneous uploads

---

## 🛠️ Troubleshooting

### **CORS Errors**
- Open browser console
- Check if API is running on correct port
- Verify CORS origins in `api.py`

### **File Upload Fails**
- Check file size (max 50MB by default)
- Verify file is valid PDF
- Check temp upload directory permissions

### **Slow Processing**
- Large PDFs take longer
- Check server resources (CPU/RAM)
- Consider increasing timeout limits

---

## 📝 Testing

Run test client:
```bash
python test_api.py
```

Or test with cURL:
```bash
# Health check
curl http://localhost:8000/health

# Upload file
curl -X POST "http://localhost:8000/extract" \
  -F "file=@test.pdf"
```

---

## 🎯 Next Steps

1. ✅ API is ready to use
2. Add authentication for production
3. Deploy to cloud (AWS, GCP, Azure)
4. Set up monitoring and logging
5. Add webhooks for job completion
6. Implement caching for repeated files

---

**Need help? Check the interactive docs at http://localhost:8000/docs**
