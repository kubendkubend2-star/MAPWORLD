@echo off
echo ===================================================
echo     LAUNCHING GAMEDEV JOURNEY 2.0 WEB APPLICATION
echo ===================================================
echo.
python database.py
echo Starting server at http://127.0.0.1:5000 ...
python app.py
pause
