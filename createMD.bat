@echo off
cd /d C:\workspace\vscode\python\RSSCrawler\-AI-RSSCrawler
call venv\Scripts\activate.bat
python createMD.py
venv\Scripts\deactivate.bat