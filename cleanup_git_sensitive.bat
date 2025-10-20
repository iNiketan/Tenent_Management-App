@echo off
REM ============================================
REM Remove sensitive files from Git history
REM ============================================

echo ========================================
echo Git Cleanup - Remove Sensitive Files
echo ========================================
echo.
echo This script will remove sensitive files from Git
echo WARNING: This rewrites Git history!
echo.

pause

echo.
echo [1/4] Checking for sensitive files in Git...
echo.

REM Check what sensitive files are currently tracked
git ls-files | findstr /I ".env" && echo FOUND: .env files
git ls-files | findstr /I ".sqlite3" && echo FOUND: Database files
git ls-files | findstr /I ".pdf" && echo FOUND: PDF files
git ls-files | findstr /I "ngrok" && echo FOUND: Ngrok files

echo.
echo [2/4] Removing from Git cache...
echo.

REM Remove from staging (if recently added)
git rm --cached .env 2>nul
git rm --cached db.sqlite3 2>nul
git rm --cached *.pdf 2>nul
git rm --cached ngrok.exe 2>nul

REM Remove from all commits (use with caution!)
REM Uncomment the following lines if files are in Git history
REM git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .env" --prune-empty --tag-name-filter cat -- --all
REM git filter-branch --force --index-filter "git rm --cached --ignore-unmatch db.sqlite3" --prune-empty --tag-name-filter cat -- --all

echo.
echo [3/4] Current status:
echo.
git status

echo.
echo [4/4] Next steps:
echo ========================================
echo 1. Review the changes above
echo 2. If satisfied, commit the changes:
echo    git add .gitignore
echo    git commit -m "Update .gitignore and remove sensitive files"
echo.
echo 3. Force push (if you rewrote history):
echo    git push origin --force --all
echo    WARNING: Only do this if no one else is using the repo!
echo ========================================
echo.

pause

