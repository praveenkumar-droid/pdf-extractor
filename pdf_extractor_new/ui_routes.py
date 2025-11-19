"""
Web UI Server - Serves the HTML interface properly
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# This will be mounted in the main API
def setup_ui_routes(app: FastAPI):
    """Add UI routes to the main FastAPI app"""
    
    @app.get("/ui", response_class=HTMLResponse)
    async def serve_ui():
        """Serve the web UI"""
        ui_path = Path(__file__).parent / "web_ui.html"
        with open(ui_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @app.get("/")
    async def root_redirect():
        """Redirect root to UI"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/ui" />
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                }
                h1 { font-size: 48px; margin-bottom: 20px; }
                p { font-size: 20px; opacity: 0.9; }
                .links {
                    margin-top: 40px;
                }
                a {
                    color: white;
                    text-decoration: none;
                    background: rgba(255,255,255,0.2);
                    padding: 15px 30px;
                    border-radius: 10px;
                    display: inline-block;
                    margin: 10px;
                    transition: all 0.3s;
                }
                a:hover {
                    background: rgba(255,255,255,0.3);
                    transform: translateY(-2px);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 PDF Text Extractor</h1>
                <p>Redirecting to Web UI...</p>
                <div class="links">
                    <a href="/ui">🎨 Web UI</a>
                    <a href="/docs">📖 API Docs</a>
                    <a href="/redoc">📚 ReDoc</a>
                </div>
            </div>
        </body>
        </html>
        """)
