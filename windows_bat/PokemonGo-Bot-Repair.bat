TITLE PokemonGo-Bot Repair
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
@ECHO --------------------Creating Backup--------------------
@ECHO.
@ECHO.
@ECHO.
RMDIR C:\Python27\Backup /s /q
MKDIR C:\Python27\Backup
COPY C:\Python27\PokemonGo-Bot\encrypt*.* C:\Python27\Backup
COPY C:\Python27\PokemonGo-Bot\configs\config.json C:\Python27\Backup
COPY C:\Python27\PokemonGo-Bot\web\config\userdata.js C:\Python27\Backup
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Downloading PokemonGo-Bot--------------------
@ECHO.
@ECHO.
@ECHO.
RMDIR C:\Python27\PokemonGo-Bot /s /q
cd C:\Python27\
pip2 install --upgrade pip
pip2 install --upgrade virtualenv
pip2 install --upgrade "%~dp0\PyYAML-3.11-cp27-cp27m-win32.whl"
pip2 install --upgrade "%~dp0\PyYAML-3.11-cp27-cp27m-win_amd64.whl"
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Restoring Backup--------------------
@ECHO.
@ECHO.
@ECHO.
COPY C:\Python27\Backup\encrypt*.* C:\Python27\PokemonGo-Bot\
COPY C:\Python27\Backup\config.json C:\Python27\PokemonGo-Bot\configs\
COPY C:\Python27\Backup\userdata.js C:\Python27\PokemonGo-Bot\web\config\
RMDIR C:\Python27\Backup /s /q
@ECHO.
@ECHO.
@ECHO.
@PAUSE