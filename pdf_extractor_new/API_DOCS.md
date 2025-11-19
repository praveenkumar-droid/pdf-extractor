# FastAPI REST API Documentation

Complete REST API for Japanese PDF text extraction.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server

**Windows:**
```bash
start_api.bat
```

**Linux/Mac:**
```bash
chmod +x start_api.sh
./start_api.sh
```

**Manual:**
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Access API

- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## 📡 API Endpoints

### 1. Health Check

**GET /** or **GET /health**

Check if API is running

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-06T14:30:22",
  "directories": {...},
  "config": {...}
}
```

---

### 2. Extract Single PDF

**POST /extract**

Upload and extract text from a single PDF

**Parameters:**
- `file` (required): PDF file
- `normalize` (optional): Override character normalization
- `remove_headers` (optional): Override header/footer removal

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/extract" \
  -F "file=@document.pdf"
```

**Example (Python):**
```python
import requests

with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/extract',
        files={'file': f}
    )

result = response.json()
print(result['extracted_text'])
```

**Example (JavaScript/fetch):**
```javascript
const formData = new FormData();
formData.append('file', pdfFile);

const response = await fetch('http://localhost:8000/extract', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.extracted_text);
```

**Response:**
```json
{
  "success": true,
  "file_id": "abc123...",
  "filename": "document.pdf",
  "extracted_text": "第1章\n序論\n...",
  "metadata": {
    "character_count": 12500,
    "line_count": 450,
    "processing_time_seconds": 2.34,
    "timestamp": "20241106_143022"
  },
  "download_url": "/download/abc123..."
}
```

---

### 3. Extract Multiple PDFs (Batch)

**POST /extract/batch**

Upload and extract text from multiple PDFs

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/extract/batch" \
  -F "files=@doc1.pdf" \
  -F "files=@doc2.pdf" \
  -F "files=@doc3.pdf"
```

**Example (Python):**
```python
import requests

files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.pdf', 'rb')),
    ('files', open('doc3.pdf', 'rb'))
]

response = requests.post(
    'http://localhost:8000/extract/batch',
    files=files
)

result = response.json()
print(f"Processed: {result['successful']}/{result['total_files']}")
```

**Response:**
```json
{
  "batch_id": "xyz789...",
  "timestamp": "20241106_143022",
  "total_files": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "filename": "doc1.pdf",
      "success": true,
      "file_id": "abc123...",
      "character_count": 8500,
      "processing_time_seconds": 1.5,
      "download_url": "/download/abc123..."
    },
    ...
  ]
}
```

---

### 4. Process Input Folder

**POST /extract/folder**

Process all PDFs in the `input/` directory

**Example:**
```bash
curl -X POST "http://localhost:8000/extract/folder"
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_files": 50,
    "successful": 48,
    "failed": 2,
    "skipped": 10,
    "success_rate": "96.0%"
  },
  "failed_files": [
    {"file": "corrupted.pdf", "error": "..."}
  ],
  "input_directory": "D:\\pdf_extractor_new\\input",
  "output_directory": "D:\\pdf_extractor_new\\output"
}
```

---

### 5. Download Extracted Text

**GET /download/{file_id}**

Download extracted text file

**Example:**
```bash
curl "http://localhost:8000/download/abc123..." -o extracted.txt
```

**Example (Python):**
```python
response = requests.get(f'http://localhost:8000/download/{file_id}')
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(response.text)
```

---

### 6. Get Statistics

**GET /stats**

Get processing statistics

**Example:**
```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "files": {
    "input_pdfs": 25,
    "output_texts": 48,
    "log_files": 12
  },
  "directories": {...},
  "latest_report": {...}
}
```

---

### 7. Get Configuration

**GET /config**

Get current configuration settings

**Example:**
```bash
curl http://localhost:8000/config
```

---

### 8. Cleanup Files

**DELETE /cleanup**

Delete temporary files

**Parameters:**
- `cleanup_uploads` (optional): Delete uploaded files
- `cleanup_outputs` (optional): Delete output files  
- `cleanup_logs` (optional): Delete log files

**Example:**
```bash
curl -X DELETE "http://localhost:8000/cleanup?cleanup_uploads=true"
```

---

## 🔌 Integration Examples

### Node.js / Express

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function extractPDF(filePath) {
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  
  const response = await axios.post(
    'http://localhost:8000/extract',
    form,
    { headers: form.getHeaders() }
  );
  
  return response.data;
}
```

### React Frontend

```javascript
async function uploadPDF(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result.extracted_text;
}
```

### Python Microservice

```python
import requests

def extract_pdf_service(pdf_bytes, filename):
    files = {'file': (filename, pdf_bytes, 'application/pdf')}
    response = requests.post(
        'http://localhost:8000/extract',
        files=files
    )
    return response.json()
```

---

## 🎯 Use Cases

### 1. Web Application
Upload PDFs via web interface → Extract → Display text

### 2. Microservice Architecture
Health IQ backend calls extraction API for medical documents

### 3. Batch Processing
Automated system processes folders of PDFs nightly

### 4. Mobile App Backend
Mobile app uploads PDFs → API extracts → Returns text to app

---

## 🔒 Production Considerations

### Security
```python
# Add authentication
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/extract")
async def extract_pdf(
    file: UploadFile,
    token: str = Depends(security)
):
    # Verify token
    ...
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/extract")
@limiter.limit("10/minute")
async def extract_pdf(...):
    ...
```

### CORS Configuration
```python
# Production CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### File Size Limits
```python
from fastapi import UploadFile, File

@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(..., max_length=10_000_000)  # 10MB
):
    ...
```

---

## 📊 Performance

- **Single PDF (10 pages):** ~1-2 seconds
- **Batch (10 PDFs):** ~10-20 seconds
- **Large PDF (100 pages):** ~10-15 seconds
- **Concurrent requests:** Limited by CPU cores

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Change port
uvicorn api:app --port 8001
```

### CORS Errors
Check `allow_origins` in api.py

### File Upload Fails
Check file size limits and multipart form data

### Extraction Errors
Check logs in `logs/` directory

---

## 📝 Testing

### Interactive Docs (Swagger UI)
http://localhost:8000/docs

### Test Script
```bash
python test_api.py
```

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Extract PDF
curl -X POST "http://localhost:8000/extract" \
  -F "file=@test.pdf" \
  | jq .
```

---

## 🚀 Deployment

### Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Systemd Service
```ini
[Unit]
Description=PDF Extractor API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/pdf_extractor_new
ExecStart=/usr/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 📚 Additional Resources

- FastAPI Docs: https://fastapi.tiangolo.com
- Uvicorn Docs: https://www.uvicorn.org
- API Testing: http://localhost:8000/docs
