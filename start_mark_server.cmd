@echo off
cd /d "C:\u-claw\portable\data\.openclaw\workspace"
echo Server running at http://localhost:8765
echo Open in browser and click on moles!
start http://localhost:8765/mark_mole.html
python -m http.server 8765
pause
