@echo off
chcp 65001 >nul
start /B /MIN "" "C:\Program Files\Python311\python.exe" "%~dp0binarizer_gui.py"
timeout /t 2 >nul
exit
