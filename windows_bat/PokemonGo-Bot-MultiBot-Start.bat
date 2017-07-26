TITLE PokemonGo-Bot
CLS
@ECHO OFF



:init
setlocal DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
set "batchPath=%~0"
for %%k in (%0) do set batchName=%%~nk
set "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
setlocal EnableDelayedExpansion



:checkPrivileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges ) else ( goto getPrivileges )



:getPrivileges
if '%1'=='ELEV' (echo ELEV & shift /1 & goto gotPrivileges)
@ECHO Set UAC = CreateObject^("Shell.Application"^) > "%vbsGetPrivileges%"
@ECHO args = "ELEV " >> "%vbsGetPrivileges%"
@ECHO For Each strArg in WScript.Arguments >> "%vbsGetPrivileges%"
@ECHO args = args ^& strArg ^& " " >> "%vbsGetPrivileges%"
@ECHO Next >> "%vbsGetPrivileges%"
@ECHO UAC.ShellExecute "!batchPath!", args, "", "runas", 1 >> "%vbsGetPrivileges%"
"%SystemRoot%\System32\WScript.exe" "%vbsGetPrivileges%" %*
exit /B



:gotPrivileges
setlocal & pushd .
cd /d %~dp0
if '%1'=='ELEV' (del "%vbsGetPrivileges%" 1>nul 2>nul & shift /1)



:startBot
REM CLS
REM ECHO.
REM ECHO.
REM ECHO --------------------Initializing web server--------------------
REM ECHO.
REM ECHO.
REM set BatchPath="%~dp0"
REM start cmd.exe /k "CD %BatchPath%&CD..&CD web&python -m SimpleHTTPServer"
REM ECHO.
REM ECHO.
CLS
ECHO --------------------Starting bot--------------------
ECHO.
ECHO.



:loop
TITLE=PokemonGo-Bot
CD %BatchPath%
CD ..
python MultiBot.py
if errorlevel 1 goto restart
if errorlevel 0 goto eof

:eof
exit
