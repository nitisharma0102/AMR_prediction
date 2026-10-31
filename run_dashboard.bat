@echo off
title Clinical AMR Diagnostic Dashboard
echo ====================================================================
echo Starting Clinical AMR Diagnostic Decision Support System...
echo ====================================================================
cd /d "%~dp0"
python -m streamlit run app/app.py
pause

