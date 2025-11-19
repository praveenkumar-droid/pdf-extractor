"""
Simple script to start the FastAPI server
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting PDF Extractor API...")
    print("📖 API Docs will be available at: http://localhost:8000/docs")
    print("📊 ReDoc will be available at: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
