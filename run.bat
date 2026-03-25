@echo off
setlocal

:menu
cls
echo ==========================================
echo AI News Content Analysis - Command Menu
echo ==========================================
echo 1. Initialize / Reset Database
echo 2. Run Full Crawl (All Sources, Limit 50)
echo 3. Crawl VNExpress Only
echo 4. Crawl TuoiTre Only
echo 5. Check VNExpress (Test Script)
echo 6. Check TuoiTre (Test Script)
echo 0. Exit
echo ==========================================
set /p choice="Enter your choice (0-6): "

if "%choice%"=="1" goto init
if "%choice%"=="2" goto crawl_all
if "%choice%"=="3" goto crawl_vnexpress
if "%choice%"=="4" goto crawl_tuoitre
if "%choice%"=="5" goto check_vnexpress
if "%choice%"=="6" goto check_tuoitre
if "%choice%"=="0" goto end
goto menu

:init
echo Initializing database...
python src\main.py setup
pause
goto menu

:crawl_all
echo Running full crawl...
python src\main.py ingest --source all --limit 50
pause
goto menu

:crawl_vnexpress
echo Crawling VNExpress...
python src\main.py ingest --source vnexpress
pause
goto menu

:crawl_tuoitre
echo Crawling TuoiTre...
python src\main.py ingest --source tuoitre
pause
goto menu

:check_vnexpress
echo Running crawler tests...
python src\main.py check
pause
goto menu

:check_tuoitre
echo Running crawler tests...
python src\main.py check
pause
goto menu

:end
exit /b
