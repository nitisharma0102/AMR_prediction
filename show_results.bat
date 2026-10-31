@echo off
title Benchmark Results and Performance Tables
echo ====================================================================
echo Displaying Multi-Model Benchmark and Clinical Metric Tables...
echo ====================================================================
cd /d "%~dp0"
python show_results.py
pause

