TITLE PokemonGo-Bot
@ECHO OFF
CLS
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%

:init
setlocal DisableDelayedExpansion
set "batchPath=%~0"
for %%k in (%0) do set batchName=%%~nk
set "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
setlocal EnableDelayedExpansion

:checkPrivileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges ) else ( goto getPrivileges )

:getPrivileges
if '%1'=='ELEV' (echo ELEV & shift /1 & goto gotPrivileges)
ECHO.

ECHO Set UAC = CreateObject^("Shell.Application"^) > "%vbsGetPrivileges%"
ECHO args = "ELEV " >> "%vbsGetPrivileges%"
ECHO For Each strArg in WScript.Arguments >> "%vbsGetPrivileges%"
ECHO args = args ^& strArg ^& " "  >> "%vbsGetPrivileges%"
ECHO Next >> "%vbsGetPrivileges%"
ECHO UAC.ShellExecute "!batchPath!", args, "", "runas", 1 >> "%vbsGetPrivileges%"
"%SystemRoot%\System32\WScript.exe" "%vbsGetPrivileges%" %*
exit /B

:gotPrivileges
setlocal & pushd .
cd /d %~dp0
if '%1'=='ELEV' (del "%vbsGetPrivileges%" 1>nul 2>nul  &  shift /1)

call:ech
@ECHO --------------------Verifying PokemonGo-Bot version--------------------
call:ech
cd C:/Python27/PokemonGo-Bot/
git pull
git submodule update --init --recursive
git submodule foreach git pull origin master
call:ech
@ECHO WARNING: Verify if the Config.json file got updated. If Yes, check if your modifications are still valid before proceeding.
call:ech
@timeout /t 10
cls
call:ech
@ECHO --------------------Initializing environment--------------------
call:ech
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
@timeout /t 10
cls
call:ech
@ECHO --------------------Initializing web server--------------------
call:ech
start cmd.exe /k "cd C:/Python27/PokemonGo-Bot/web&python -m SimpleHTTPServer"
@timeout /t 10
cls
call:ech
@ECHO --------------------Starting bot--------------------
call:ech
:loop
TITLE=PokemonGo-Bot 
python C:/Python27/PokemonGo-Bot/pokecli.py
if errorlevel 1 goto restart
if errorlevel 0 goto eof
:restart
call:w8
timeout /t 60
goto loop
goto:eof
:ech
@ECHO.
@ECHO.
goto:eof
:w8
call:ech
ECHO. OEPS, something went wrong ^^! It needs your attention ^^!
call:ech
goto:eof
:eof
exit
