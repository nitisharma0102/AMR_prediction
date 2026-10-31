@echo off
setlocal
echo =======================================================
echo   AMR-ProkBERT: Automatic GitHub Push Utility
echo =======================================================
echo.

set "GIT_EXE=C:\Users\HP\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe"

if not exist "%GIT_EXE%" (
    echo [ERROR] Git executable not found at: %GIT_EXE%
    pause
    exit /b 1
)

echo Step 1: Make sure you have created an EMPTY repository on GitHub:
echo         Go to: https://github.com/new
echo         Repository name: e.g. AMR-ProkBERT-Capstone
echo         (Leave "Initialize this repository with README" UNCHECKED)
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/nitisharmaa0102/AMR-ProkBERT-Capstone.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL entered. Aborted.
    pause
    exit /b 1
)

echo.
echo Linking remote repository...
"%GIT_EXE%" remote remove origin 2>nul
"%GIT_EXE%" remote add origin %REPO_URL%

echo.
echo Pushing branch 'main' to GitHub...
"%GIT_EXE%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo   SUCCESS! All code has been pushed to GitHub!
    echo =======================================================
) else (
    echo.
    echo [!] Push encountered an error. If prompted, please complete
    echo     the GitHub login in the browser window.
)

echo.
pause

