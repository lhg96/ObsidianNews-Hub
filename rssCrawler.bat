@echo off
cd /d C:\workspace\vscode\python\RSSCrawler\-AI-RSSCrawler
call venv\Scripts\activate.bat
python rssCrawler.py
venv\Scripts\deactivate.bat