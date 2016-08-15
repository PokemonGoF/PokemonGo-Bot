TITLE PokemonGo-Bot
@ECHO OFF
CLS

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
@ECHO ON
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Verifying PokemonGo-Bot version--------------------
@ECHO.
@ECHO.
@ECHO.
cd C:/Python27/PokemonGo-Bot/
git pull
git submodule update --init --recursive
git submodule foreach git pull origin master
@ECHO.
@ECHO.
@ECHO.
@ECHO WARNING: Verify if the Config.json file got updated. If Yes, check if your modifications are still valid before proceeding.
@ECHO.
@ECHO.
@ECHO.
@pause
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Initializing environment--------------------
@ECHO.
@ECHO.
@ECHO.
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Initializing web server--------------------
@ECHO.
@ECHO.
@ECHO.
start cmd.exe /k "cd C:/Python27/PokemonGo-Bot/web&python -m SimpleHTTPServer"
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Starting bot--------------------
@ECHO.
@ECHO.
@ECHO.
python C:/Python27/PokemonGo-Bot/pokecli.py








