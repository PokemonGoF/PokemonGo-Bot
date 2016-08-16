TITLE PokemonGo-Bot Installer
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
@ECHO --------------------PokemonGo-Bot Installer--------------------
@ECHO. 
@ECHO.
@ECHO.
@ECHO Before proceeding, please install the following software:
@ECHO. 
@ECHO ---- Python 2.7.x
@ECHO      "http://docs.python-guide.org/en/latest/starting/installation/"
@ECHO.
@ECHO ---- git
@ECHO      "https://git-scm.com/book/en/v2/Getting-Started-Installing-Git"
@ECHO.
@ECHO ---- Microsoft Visual C++ Compiler for Python 2.7
@ECHO      "http://www.microsoft.com/en-us/download/details.aspx?id=44266"
@ECHO.
@ECHO ---- encrypt.so / encrypt.dll or encrypt_64.dll (Copy to the same folder as this batch file)
@ECHO      Get them from our Slack chat! "https://pokemongo-bot.herokuapp.com/"
@ECHO.
@ECHO ---- If you already have a config.json and a userdata.js, copy to the same folder as this batch file.
@ECHO.
@ECHO.
@ECHO.
@PAUSE
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Checking Installation Path--------------------
@ECHO.
if "%~dp0"=="C:\Python27\PokemonGo-Bot\windows_bat\" (
COPY "C:\Python27\PokemonGo-Bot\windows_bat\PokemonGo-Bot-Install.bat" "C:\Python27\"
CALL "C:\Python27\PokemonGo-Bot-Install.bat"
end.
) ELSE (
@ECHO Installation Path OK! Proceeding!
)
@ECHO.
@ECHO --------------------Creating Backup--------------------
@ECHO.
@ECHO.
@ECHO.
COPY C:\Python27\PokemonGo-Bot\encrypt*.* "%~dp0\"
COPY C:\Python27\PokemonGo-Bot\configs\config.json "%~dp0\"
COPY C:\Python27\PokemonGo-Bot\web\config\userdata.js "%~dp0\"
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Downloading PokemonGo-Bot--------------------
@ECHO.
@ECHO.
@ECHO.
@ECHO.
RMDIR C:\Python27\PokemonGo-Bot /s /q
cd C:\Python27\
pip2 install --upgrade pip
pip2 install --upgrade virtualenv
pip2 install --upgrade protobuf==3.0.0b4
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot
pip2 install --upgrade "C:\Python27\PokemonGo-Bot\windows_bat\PyYAML-3.11-cp27-cp27m-win32.whl"
pip2 install --upgrade "C:\Python27\PokemonGo-Bot\windows_bat\PyYAML-3.11-cp27-cp27m-win_amd64.whl"
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
cd C:/Python27/PokemonGo-Bot/
virtualenv .
call C:\Python27\PokemonGo-Bot\Scripts\activate.bat
pip2 install --upgrade -r C:/Python27/PokemonGo-Bot/requirements.txt
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Copying additional files--------------------
@ECHO.
@ECHO.
@ECHO.
COPY "%~dp0\encrypt*.*" C:\Python27\PokemonGo-Bot\
COPY "%~dp0\config.json" C:\Python27\PokemonGo-Bot\configs\
COPY "%~dp0\userdata.js" C:\Python27\PokemonGo-Bot\web\config\
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------File customization--------------------
@ECHO.
@ECHO.
@ECHO.
@ECHO Remember to configure both config.json and userdata.js!
@ECHO.
@ECHO "C:/Python27/PokemonGo-Bot/configs/config.json"
@ECHO INSTRUCTIONS:
@ECHO "https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/configuration_files.md"
@ECHO.
@ECHO "C:/Python27/PokemonGo-Bot/web/config/userdata.js"
@ECHO INSTRUCTIONS:
@ECHO "https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/google_map.md"
@ECHO.
@ECHO To get an Google Map API Key:
@ECHO "https://developers.google.com/maps/documentation/javascript/get-api-key"
@ECHO.
@ECHO.
@ECHO.
@PAUSE
