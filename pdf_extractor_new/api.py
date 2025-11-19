"""
FastAPI REST API for PDF Text Extraction
High-performance async API with file upload support
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime
import json
import asyncio

from extractor import JapanesePDFExtractor
from processor import FileSystemProcessor
from ui_routes import setup_ui_routes
import config

# Initialize FastAPI app
app = FastAPI(
    title="Japanese PDF Text Extractor API",
    description="Extract text from Japanese PDFs with perfect reading order",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize extractor
extractor = JapanesePDFExtractor()
processor = FileSystemProcessor()

# Temporary upload directory
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Store processing jobs
processing_jobs = {}


# Setup UI routes
setup_ui_routes(app)


@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    print("="*60)
    print("🚀 PDF Extractor API Started")
    print("="*60)
    print(f"🎨 Web UI:  http://localhost:8000/ui")
    print(f"📖 API Docs: http://localhost:8000/docs")
    print(f"📚 ReDoc:    http://localhost:8000/redoc")
    print(f"📁 Input:    {config.INPUT_DIR}")
    print(f"📁 Output:   {config.OUTPUT_DIR}")
    print("="*60)





@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "extractor": "ready",
        "input_dir": str(config.INPUT_DIR),
        "output_dir": str(config.OUTPUT_DIR)
    }


# Thread lock for config modifications
import threading
_config_lock = threading.Lock()

@app.post("/extract")
async def extract_single_pdf(
    file: UploadFile = File(...),
    normalize: bool = Query(False, description="Normalize characters (disabled by default per extraction rules)"),
    fix_spacing: bool = Query(True, description="Fix spacing"),
    remove_headers: bool = Query(True, description="Remove headers/footers")
):
    """
    Extract text from a single PDF file
    
    **Parameters:**
    - **file**: PDF file to extract (required)
    - **normalize**: Normalize half-width to full-width characters (default: false - preserves original)
    - **fix_spacing**: Fix spacing between Japanese and English (default: true)
    - **remove_headers**: Remove headers, footers, page numbers (default: true)
    
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
        
        # Thread-safe config modification
        with _config_lock:
            # Store original config values
            original_normalize = config.NORMALIZE_CHARACTERS
            original_spacing = config.FIX_SPACING
            original_headers = config.REMOVE_HEADERS_FOOTERS
            
            try:
                # Apply request-specific settings
                config.NORMALIZE_CHARACTERS = normalize
                config.FIX_SPACING = fix_spacing
                config.REMOVE_HEADERS_FOOTERS = remove_headers
                
                # Create fresh extractor instance for this request
                local_extractor = JapanesePDFExtractor()
                
                # Extract text
                text = local_extractor.extract_pdf(str(temp_path))
            finally:
                # Always restore config
                config.NORMALIZE_CHARACTERS = original_normalize
                config.FIX_SPACING = original_spacing
                config.REMOVE_HEADERS_FOOTERS = original_headers
        
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
    background_tasks: BackgroundTasks = None
):
    """
    Extract text from multiple PDF files
    
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
    processing_jobs[job_id] = {
        "status": "processing",
        "total": len(files),
        "completed": 0,
        "failed": 0,
        "results": [],
        "started_at": datetime.now().isoformat()
    }
    
    # Process files in background
    background_tasks.add_task(process_batch, job_id, files)
    
    return {
        "success": True,
        "job_id": job_id,
        "total_files": len(files),
        "message": "Batch processing started",
        "check_status": f"/jobs/{job_id}"
    }


async def process_batch(job_id: str, files: List[UploadFile]):
    """Background task to process multiple files"""
    for file in files:
        temp_id = str(uuid.uuid4())
        temp_path = UPLOAD_DIR / f"{temp_id}_{file.filename}"
        
        try:
            # Save file
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract
            text = extractor.extract_pdf(str(temp_path))
            
            # Store result
            processing_jobs[job_id]["results"].append({
                "filename": file.filename,
                "success": True,
                "text": text,
                "characters": len(text)
            })
            processing_jobs[job_id]["completed"] += 1
        
        except Exception as e:
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
    processing_jobs[job_id]["status"] = "completed"
    processing_jobs[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of a batch processing job
    
    **Parameters:**
    - **job_id**: Job ID returned from /extract/batch
    
    **Returns:**
    - Job status and results
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]


@app.post("/extract/folder")
async def extract_from_folder(
    background_tasks: BackgroundTasks,
    input_path: Optional[str] = Query(None, description="Custom input folder path")
):
    """
    Extract all PDFs from the input folder
    
    **Parameters:**
    - **input_path**: Optional custom input folder (default: configured input folder)
    
    **Returns:**
    - Job ID for tracking progress
    """
    # Create job
    job_id = str(uuid.uuid4())
    processing_jobs[job_id] = {
        "status": "processing",
        "type": "folder",
        "started_at": datetime.now().isoformat()
    }
    
    # Process in background
    background_tasks.add_task(process_folder, job_id, input_path)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Folder processing started",
        "check_status": f"/jobs/{job_id}"
    }


async def process_folder(job_id: str, input_path: Optional[str]):
    """Background task to process entire folder"""
    try:
        # Create processor
        if input_path:
            proc = FileSystemProcessor(input_dir=input_path)
        else:
            proc = processor
        
        # Process all files
        stats = proc.process_all()
        
        # Update job
        processing_jobs[job_id].update({
            "status": "completed",
            "statistics": stats,
            "completed_at": datetime.now().isoformat()
        })
    
    except Exception as e:
        processing_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })


@app.get("/download/{filename}")
async def download_result(filename: str):
    """
    Download extracted text file
    
    **Parameters:**
    - **filename**: Name of the text file (without .txt extension)
    
    **Returns:**
    - Text file download
    """
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
    """
    List all extracted files
    
    **Returns:**
    - List of available extracted files
    """
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
    """
    List all processing logs
    
    **Returns:**
    - List of available log files
    """
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
    """
    Get content of a log or report file
    
    **Parameters:**
    - **filename**: Log or report filename
    
    **Returns:**
    - File content
    """
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
    """
    Delete a completed job from memory
    
    **Parameters:**
    - **job_id**: Job ID to delete
    
    **Returns:**
    - Success message
    """
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    del processing_jobs[job_id]
    
    return {
        "success": True,
        "message": f"Job {job_id} deleted"
    }


@app.get("/stats")
async def get_stats():
    """
    Get overall system statistics
    
    **Returns:**
    - System statistics
    """
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
    
    return {
        "input_pdfs": len(input_pdfs),
        "output_texts": len(output_texts),
        "log_files": len(log_files),
        "active_jobs": len([j for j in processing_jobs.values() if j["status"] == "processing"]),
        "latest_report": latest_report
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
