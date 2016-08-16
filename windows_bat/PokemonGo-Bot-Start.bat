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
CLS
@ECHO --------------------Verifying PokemonGo-Bot version--------------------
@ECHO.
CD..
git pull
git submodule update --init --recursive
@ECHO.
@ECHO WARNING: Verify if the Config.json file got updated. If Yes, check if your modifications are still valid before proceeding.
@ECHO.
@timeout /t 10
CLS
@ECHO --------------------Initializing environment--------------------
@ECHO.
virtualenv .
CD Scripts
call activate.bat
CD..
pip2 install --upgrade -r requirements.txt
CLS
@ECHO --------------------Initializing web server--------------------
@ECHO.
set BatchPath="%~dp0"
start cmd.exe /k "CD %BatchPath%&CD..&CD web&python -m SimpleHTTPServer"
@ECHO.
CLS
@ECHO --------------------Starting bot--------------------
@ECHO.



:loop
TITLE=PokemonGo-Bot
CD %BatchPath%
CD ..
python pokecli.py
if errorlevel 1 goto restart
if errorlevel 0 goto eof



:restart
call:problem
timeout /t 60
goto loop
goto:eof



:problem
@ECHO.
@ECHO. Something went wrong and the bot needed to be restarted. Please investigate the cause.
@ECHO.
goto:eof



:eof
exit
