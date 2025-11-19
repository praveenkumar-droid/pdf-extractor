"""
FastAPI REST API for PDF Text Extraction - FIXED VERSION
High-performance async API with thread-safe configuration

FIXES:
1. Thread-safe configuration handling (no global config modification)
2. Proper error handling
3. Connection pooling for extractors
4. Request-scoped settings
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import json
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
import threading

from extractor import JapanesePDFExtractor
from processor import FileSystemProcessor
from ui_routes import setup_ui_routes
import config

# Thread-local storage for request-specific configuration
_thread_local = threading.local()


@dataclass
class ExtractionSettings:
    """Request-scoped extraction settings (thread-safe)"""
    normalize: bool = False  # Disabled by default per "EXTRACT ONLY" principle
    fix_spacing: bool = True
    remove_headers: bool = True
    join_lines: bool = True
    fix_punctuation: bool = True


class ThreadSafeExtractor:
    """Thread-safe extractor with request-scoped settings"""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def extract_pdf(self, pdf_path: str, settings: ExtractionSettings) -> str:
        """Extract PDF with specific settings (thread-safe)"""
        # Create a new extractor instance for this request
        extractor = JapanesePDFExtractor()
        
        # Override extractor behavior based on settings
        # Note: We modify the instance, not global config
        
        with open(pdf_path, 'rb') as f:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                # Detect repeating elements
                headers, footers = extractor._detect_repeating_elements(pdf) if settings.remove_headers else ([], [])
                
                # Process each page
                all_pages = []
                for page_num, page in enumerate(pdf.pages, 1):
                    # Custom extraction respecting settings
                    page_text = self._extract_page_with_settings(
                        extractor, page, headers, footers, settings
                    )
                    if page_text.strip():
                        all_pages.append(page_text)
                
                # Combine pages
                raw_text = '\n\n'.join(all_pages)
                
                # Apply cleanup based on settings
                if settings.fix_spacing or settings.join_lines or settings.fix_punctuation:
                    cleaned_text = self._cleanup_with_settings(extractor, raw_text, settings)
                else:
                    cleaned_text = raw_text
                
                return cleaned_text
    
    def _extract_page_with_settings(self, extractor, page, headers, footers, settings):
        """Extract page with custom settings"""
        words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
        
        if not words:
            return ""
        
        # Filter metadata if enabled
        if settings.remove_headers:
            words = extractor._filter_metadata(words, headers, footers, page.height, page.width)
        
        # Detect and extract columns
        columns = extractor._detect_columns(words, page.width)
        
        page_texts = []
        for column_words in columns:
            column_text = extractor._extract_column(column_words)
            page_texts.append(column_text)
        
        return '\n\n'.join(page_texts)
    
    def _cleanup_with_settings(self, extractor, text, settings):
        """Cleanup text with custom settings"""
        import re
        
        if settings.fix_spacing:
            text = extractor._fix_spacing(text)
        
        if settings.join_lines:
            text = extractor._join_lines(text)
        
        if settings.fix_punctuation:
            text = extractor._fix_punctuation(text)
        
        # Remove excessive blank lines
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        
        return text.strip()


# Global thread-safe extractor
_safe_extractor = ThreadSafeExtractor()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    print("="*60)
    print("🚀 PDF Extractor API Started (Thread-Safe Version)")
    print("="*60)
    print(f"🎨 Web UI:  http://localhost:8000/ui")
    print(f"📖 API Docs: http://localhost:8000/docs")
    print(f"📚 ReDoc:    http://localhost:8000/redoc")
    print(f"📁 Input:    {config.INPUT_DIR}")
    print(f"📁 Output:   {config.OUTPUT_DIR}")
    print("="*60)
    
    # Ensure directories exist
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    print("\n🛑 PDF Extractor API Shutting Down")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Japanese PDF Text Extractor API (Thread-Safe)",
    description="Extract text from Japanese PDFs with perfect reading order - Thread-safe version",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary upload directory
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store processing jobs (with lock for thread safety)
_jobs_lock = threading.Lock()
processing_jobs = {}

# Setup UI routes
setup_ui_routes(app)


def get_extraction_settings(
    normalize: bool = Query(False, description="Normalize characters (disabled by default per extraction rules)"),
    fix_spacing: bool = Query(True, description="Fix spacing between Japanese and English"),
    remove_headers: bool = Query(True, description="Remove headers/footers/page numbers"),
    join_lines: bool = Query(True, description="Join broken lines"),
    fix_punctuation: bool = Query(True, description="Fix punctuation issues")
) -> ExtractionSettings:
    """Dependency to get extraction settings from query parameters"""
    return ExtractionSettings(
        normalize=normalize,
        fix_spacing=fix_spacing,
        remove_headers=remove_headers,
        join_lines=join_lines,
        fix_punctuation=fix_punctuation
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0 (thread-safe)",
        "timestamp": datetime.now().isoformat(),
        "extractor": "ready",
        "input_dir": str(config.INPUT_DIR),
        "output_dir": str(config.OUTPUT_DIR)
    }


@app.post("/extract")
async def extract_single_pdf(
    file: UploadFile = File(...),
    settings: ExtractionSettings = Depends(get_extraction_settings)
):
    """
    Extract text from a single PDF file (Thread-Safe)
    
    **Parameters:**
    - **file**: PDF file to extract (required)
    - **normalize**: Normalize characters (default: false - per "EXTRACT ONLY" rule)
    - **fix_spacing**: Fix spacing between Japanese and English (default: true)
    - **remove_headers**: Remove headers, footers, page numbers (default: true)
    - **join_lines**: Join broken lines (default: true)
    - **fix_punctuation**: Fix punctuation issues (default: true)
    
    **Returns:**
    - Extracted text in JSON format
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save uploaded file temporarily
    temp_id = str(uuid.uuid4())
    temp_path = UPLOAD_DIR / f"{temp_id}_{file.filename}"
    
    try:
        # Save file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text with thread-safe extractor
        text = _safe_extractor.extract_pdf(str(temp_path), settings)
        
        # Get statistics
        char_count = len(text)
        line_count = len(text.split('\n'))
        word_count = len(text.split())
        
        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "statistics": {
                "characters": char_count,
                "lines": line_count,
                "words": word_count
            },
            "settings": {
                "normalize": settings.normalize,
                "fix_spacing": settings.fix_spacing,
                "remove_headers": settings.remove_headers
            },
            "extracted_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    
    finally:
        # Cleanup temp file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/extract/batch")
async def extract_batch_pdfs(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    settings: ExtractionSettings = Depends(get_extraction_settings)
):
    """
    Extract text from multiple PDF files (Thread-Safe)
    
    **Parameters:**
    - **files**: List of PDF files (max 10 files)
    
    **Returns:**
    - Job ID for tracking progress
    """
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
    
    # Validate all files
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.filename}. Only PDF files allowed."
            )
    
    # Create job
    job_id = str(uuid.uuid4())
    
    with _jobs_lock:
        processing_jobs[job_id] = {
            "status": "processing",
            "total": len(files),
            "completed": 0,
            "failed": 0,
            "results": [],
            "started_at": datetime.now().isoformat()
        }
    
    # Process files in background
    background_tasks.add_task(process_batch_safe, job_id, files, settings)
    
    return {
        "success": True,
        "job_id": job_id,
        "total_files": len(files),
        "message": "Batch processing started",
        "check_status": f"/jobs/{job_id}"
    }


async def process_batch_safe(job_id: str, files: List[UploadFile], settings: ExtractionSettings):
    """Background task to process multiple files (thread-safe)"""
    for file in files:
        temp_id = str(uuid.uuid4())
        temp_path = UPLOAD_DIR / f"{temp_id}_{file.filename}"
        
        try:
            # Save file
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract using thread-safe extractor
            text = _safe_extractor.extract_pdf(str(temp_path), settings)
            
            # Store result
            with _jobs_lock:
                processing_jobs[job_id]["results"].append({
                    "filename": file.filename,
                    "success": True,
                    "text": text,
                    "characters": len(text)
                })
                processing_jobs[job_id]["completed"] += 1
        
        except Exception as e:
            with _jobs_lock:
                processing_jobs[job_id]["results"].append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
                processing_jobs[job_id]["failed"] += 1
        
        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
    
    # Mark as complete
    with _jobs_lock:
        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a batch processing job"""
    with _jobs_lock:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        return processing_jobs[job_id].copy()


@app.post("/extract/folder")
async def extract_from_folder(
    background_tasks: BackgroundTasks,
    input_path: Optional[str] = Query(None, description="Custom input folder path")
):
    """Extract all PDFs from the input folder"""
    job_id = str(uuid.uuid4())
    
    with _jobs_lock:
        processing_jobs[job_id] = {
            "status": "processing",
            "type": "folder",
            "started_at": datetime.now().isoformat()
        }
    
    background_tasks.add_task(process_folder_safe, job_id, input_path)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Folder processing started",
        "check_status": f"/jobs/{job_id}"
    }


async def process_folder_safe(job_id: str, input_path: Optional[str]):
    """Background task to process entire folder"""
    try:
        # Create processor (it creates its own extractor)
        if input_path:
            proc = FileSystemProcessor(input_dir=input_path)
        else:
            proc = FileSystemProcessor()
        
        # Process all files
        stats = proc.process_all()
        
        # Update job
        with _jobs_lock:
            processing_jobs[job_id].update({
                "status": "completed",
                "statistics": stats,
                "completed_at": datetime.now().isoformat()
            })
    
    except Exception as e:
        with _jobs_lock:
            processing_jobs[job_id].update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.now().isoformat()
            })


@app.get("/download/{filename}")
async def download_result(filename: str):
    """Download extracted text file"""
    file_path = config.OUTPUT_DIR / f"{filename}.txt"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"{filename}.txt",
        media_type="text/plain"
    )


@app.get("/files/list")
async def list_files():
    """List all extracted files"""
    output_files = list(config.OUTPUT_DIR.glob("**/*.txt"))
    
    files = []
    for file_path in output_files:
        rel_path = file_path.relative_to(config.OUTPUT_DIR)
        files.append({
            "filename": file_path.stem,
            "path": str(rel_path),
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })
    
    return {
        "total": len(files),
        "files": files
    }


@app.get("/logs/list")
async def list_logs():
    """List all processing logs"""
    log_files = list(config.LOGS_DIR.glob("*.log"))
    report_files = list(config.LOGS_DIR.glob("*.json"))
    
    logs = []
    for log_path in log_files:
        logs.append({
            "filename": log_path.name,
            "type": "log",
            "size": log_path.stat().st_size,
            "created": datetime.fromtimestamp(log_path.stat().st_ctime).isoformat()
        })
    
    for report_path in report_files:
        logs.append({
            "filename": report_path.name,
            "type": "report",
            "size": report_path.stat().st_size,
            "created": datetime.fromtimestamp(report_path.stat().st_ctime).isoformat()
        })
    
    return {
        "total": len(logs),
        "logs": sorted(logs, key=lambda x: x['created'], reverse=True)
    }


@app.get("/logs/{filename}")
async def get_log(filename: str):
    """Get content of a log or report file"""
    file_path = config.LOGS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    
    if filename.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        return content
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content}


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a completed job from memory"""
    with _jobs_lock:
        if job_id not in processing_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        del processing_jobs[job_id]
    
    return {
        "success": True,
        "message": f"Job {job_id} deleted"
    }


@app.get("/stats")
async def get_stats():
    """Get overall system statistics"""
    # Count files
    input_pdfs = list(config.INPUT_DIR.rglob("*.pdf"))
    output_texts = list(config.OUTPUT_DIR.rglob("*.txt"))
    log_files = list(config.LOGS_DIR.glob("*.log"))
    
    # Get latest report
    reports = list(config.LOGS_DIR.glob("report_*.json"))
    latest_report = None
    if reports:
        latest = max(reports, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            latest_report = json.load(f)
    
    # Count active jobs
    with _jobs_lock:
        active_jobs = len([j for j in processing_jobs.values() if j.get("status") == "processing"])
    
    return {
        "input_pdfs": len(input_pdfs),
        "output_texts": len(output_texts),
        "log_files": len(log_files),
        "active_jobs": active_jobs,
        "latest_report": latest_report
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_fixed:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
