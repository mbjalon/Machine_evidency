@echo off
Powershell.exe -NoProfile -Command "Start-Process Powershell -ArgumentList '-NoProfile -Command ""& {python app/app.py}""'"