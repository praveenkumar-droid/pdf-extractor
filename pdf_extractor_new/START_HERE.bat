@echo off
echo ========================================
echo  Starting PDF Extractor API
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server...
echo.
echo API will be available at:
echo   - http://localhost:8000/docs (Interactive docs)
echo   - http://localhost:8000/redoc (Documentation)
echo.
echo Press CTRL+C to stop the server
echo.
python start_api.py
