@echo off
set /a x=0
:LOOP
echo Running pokecli.py for count: %x%
REM Change the path for python.exe if it's different for you
C:\Python27\python.exe pokecli.py
REM Waits for 60 seconds
ping 127.0.0.1 -n 60 > nul
set /a x+=1
goto :LOOP
