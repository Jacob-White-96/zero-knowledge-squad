@echo off
start http://localhost:3000
cd frontend
python -m http.server 3000