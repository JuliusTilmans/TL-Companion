@echo off
title TrackLab - Companion - Start
echo ============================================
echo   TrackLab - Companion
echo   Social Interaction Analysis Tool
echo ============================================
echo.
echo Starting application...
echo (Your browser will open automatically)
echo (Close this window to stop the application)
echo.

set PYTHONPATH=%~dp0
"%~dp0python\python.exe" -m streamlit run "%~dp0Home_v4.py" --server.port 8501
pause
