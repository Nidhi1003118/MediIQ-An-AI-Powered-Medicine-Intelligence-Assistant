@echo off
REM Quick run script for MedBoxWeb
cd /d "%~dp0"
python -m venv .venv 2>nul
call .venv\Scripts\activate
pip install -r requirements.txt
python app.py
