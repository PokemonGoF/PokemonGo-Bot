@echo off
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

::::::::::::::::::::::::::::
::START
::::::::::::::::::::::::::::
@ECHO ON
@ECHO.
@ECHO --------------------PokemonGo-Bot Installer--------------------
@ECHO. 
@ECHO Before proceeding, please install the following software:
@ECHO. 
@ECHO ---- Python 2.7.x
@ECHO ---- http://docs.python-guide.org/en/latest/starting/installation/
@ECHO.
@ECHO ---- git
@ECHO ---- https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
@ECHO.
@ECHO ---- Protoc
@ECHO ---- https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/protoc-3.0.0-beta-4-win32.zip
@ECHO.
@ECHO ---- Microsoft Visual C++ Compiler for Python 2.7
@ECHO ---- http://www.microsoft.com/en-us/download/details.aspx?id=44266
@ECHO.
@PAUSE
@ECHO.
@ECHO --------------------Downloading PokemonGo-Bot--------------------
@ECHO.
RMDIR C:\Python27\PokemonGo-Bot /s /q
cd C:\Python27\
pip2 install --upgrade pip
pip2 install --upgrade virtualenv
pip2 install --upgrade "%~dp0\PyYAML-3.11-cp27-cp27m-win32.whl"
pip2 install --upgrade "%~dp0\PyYAML-3.11-cp27-cp27m-win_amd64.whl"
cd C:\Python27\
git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot
cd C:\Python27\PokemonGo-Bot
pip2 install --upgrade -r requirements.txt
git submodule init
git submodule update
virtualenv .
@ECHO OFF
set "VIRTUAL_ENV=C:\Python27\PokemonGo-Bot"

if defined _OLD_VIRTUAL_PROMPT (
    set "PROMPT=%_OLD_VIRTUAL_PROMPT%"
) else (
    if not defined PROMPT (
        set "PROMPT=$P$G"
    )
    set "_OLD_VIRTUAL_PROMPT=%PROMPT%"
)
set "PROMPT=(PokemonGo-Bot) %PROMPT%"

REM Don't use () to avoid problems with them in %PATH%
if defined _OLD_VIRTUAL_PYTHONHOME goto ENDIFVHOME
    set "_OLD_VIRTUAL_PYTHONHOME=%PYTHONHOME%"
:ENDIFVHOME

set PYTHONHOME=

REM if defined _OLD_VIRTUAL_PATH (
if not defined _OLD_VIRTUAL_PATH goto ENDIFVPATH1
    set "PATH=%_OLD_VIRTUAL_PATH%"
:ENDIFVPATH1
REM ) else (
if defined _OLD_VIRTUAL_PATH goto ENDIFVPATH2
    set "_OLD_VIRTUAL_PATH=%PATH%"
:ENDIFVPATH2

set "PATH=%VIRTUAL_ENV%\Scripts;%PATH%"
pip2 install --upgrade -r requirements.txt
@ECHO ON
@ECHO.
@ECHO Created by danielsdian based on information gathered from the wiki
@ECHO.
@ECHO --------------------Copying additional files--------------------
@ECHO.
COPY "%~dp0\encrypt*.*" C:\Python27\PokemonGo-Bot\
cd C:\Python27\PokemonGo-Bot\configs\
REN config.json.example config.json
cd C:\Python27\PokemonGo-Bot\web\config\
REN userdata.js.example userdata.js
@ECHO.
@ECHO --------------------File customization--------------------
@ECHO.
@ECHO Remember to configure both config.json and userdata.js!
@ECHO.
@ECHO "C:/Python27/PokemonGo-Bot/configs/config.json"
@ECHO.
@ECHO "C:/Python27/PokemonGo-Bot/web/config/userdata.js"
@ECHO.
@ECHO To get an Google Map API Key:
@ECHO https://developers.google.com/maps/documentation/javascript/get-api-key
@ECHO.
@PAUSE