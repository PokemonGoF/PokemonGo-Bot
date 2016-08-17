TITLE PokemonGo-Bot Installer
CLS
@ECHO OFF



:init
setlocal DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
set DownPathPython=https://www.python.org/ftp/python/2.7.12/
set DownPathGit=https://github.com/git-for-windows/git/releases/download/v2.9.3.windows.1/
set DownPathVisual=https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/
set VisualFName=VCForPython27.msi
set PythonFName86=python-2.7.12.msi
set PythonFName64=python-2.7.12.amd64.msi
set GitFName86=Git-2.9.3-32-bit.exe
set GitFName64=Git-2.9.3-64-bit.exe
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



:detectOS
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32-BIT || set OS=64-BIT



:CheckInstallPath
CLS
@ECHO --------------------Installation Path--------------------
@ECHO.
@ECHO.
@ECHO.
set InstallPath=
set /p InstallPath= "Choose an installation folder or press Enter to close:" ||goto:eof
FOR /F "tokens=1-4 delims=/-. " %%G IN ("%InstallPath%") DO (set InstallPath=%%G\%%H\%%I\%%J)
set PGBotPath=%InstallPath%\PokemonGo-Bot
set DownPath=%InstallPath%\Install-Files
if not exist %DownPath% md %DownPath%
if "%~dp0"=="%PGBotPath%\windows_bat\" (
COPY "%PGBotPath%\windows_bat\PokemonGo-Bot-Install.bat" %InstallPath%
CALL "%InstallPath%\PokemonGo-Bot-Install.bat"
exit.
) ELSE (
@ECHO Installation Path OK! Proceeding!
)
@ECHO.
@ECHO.
@ECHO.



:Menu
CLS
@ECHO --------------------PokemonGo-Bot Installer--------------------
@ECHO.
@ECHO.
@ECHO.
if "%OS%" == "32-BIT" (
@ECHO. 1 - Install 32-Bit software
) ELSE (
@ECHO. 1 - Install 64-Bit software
)
@ECHO.
@ECHO. 2 - Install PokemonGo-Bot
@ECHO.
@ECHO.
@ECHO.



:_choice
set _ok=
set /p _ok= Choose an option or press Enter to close: ||goto:eof
if "%OS%" == "32-BIT" IF "%_ok%" == "1" SET CHOICE=32Bit&GOTO :32Bit
if "%OS%" == "64-BIT" IF "%_ok%" == "1" SET CHOICE=64Bit&GOTO :64Bit
IF "%_ok%" == "2" SET CHOICE=InstallBot&GOTO :InstallBot
GOTO :_choice 



:32bit
CLS
@ECHO --------------------Installation of required software--------------------
@ECHO.
@ECHO Downloading Git...
if not exist %DownPath%\%GitFName86% call:getit %DownPathGit% %GitFName86%
@ECHO Downloading Python...
if not exist %DownPath%\%PythonFName86% call:getit %DownPathPython% %PythonFName86%
@ECHO Downloading Visual C++ for Python...
if not exist %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
@ECHO Installing Git...
if exist %DownPath%\%GitFName86% call:installit %GitFName86% /SILENT
@ECHO Installing Python...
if exist %DownPath%\%PythonFName86% call:installit %PythonFName86% /quiet
@ECHO Installing Visual C++ for Python...
if exist %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
@ECHO.
@ECHO.
@ECHO.
@ECHO Installation of 32-Bit software is finished.
@ECHO.
@ECHO Choose Install PokemonGo-Bot in next screen to complete.
@ECHO.
@ECHO Wait 5 seconds or press any key to continue...
@ECHO.
@ECHO.
@ECHO.
timeout /t 5 >nul
goto:Menu



:64bit
CLS
@ECHO --------------------Installation of required software--------------------
@ECHO.
@ECHO Downloading Git...
if not exist %DownPath%\%GitFName64% call:getit %DownPathGit% %GitFName64%
@ECHO Downloading Python...
if not exist %DownPath%\%PythonFName64% call:getit %DownPathPython% %PythonFName64%
@ECHO Downloading Visual C++ for Python...
if not exist %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
@ECHO Installing Git...
if exist %DownPath%\%GitFName64% call:installit %GitFName64% /SILENT
@ECHO Installing Python...
if exist %DownPath%\%PythonFName64% call:installit %PythonFName64% /quiet
@ECHO Installing Visual C++ for Python...
if exist %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
@ECHO.
@ECHO.
@ECHO.
@ECHO Installation of 64-Bit software is finished.
@ECHO.
@ECHO Choose Install PokemonGo-Bot in next screen to complete.
@ECHO.
@ECHO Wait 5 seconds or press any key to continue...
@ECHO.
@ECHO.
@ECHO.
timeout /t 5 >nul
goto:Menu



:getit
start /wait powershell -Command "Invoke-WebRequest %~1%~2 -OutFile %DownPath%\%~2"
goto:eof


:installit
start /wait %DownPath%\%~1 %~2
goto:eof



:InstallBot
CLS
@ECHO --------------------Creating Backup--------------------
@ECHO.
@ECHO.
@ECHO.
if exist %PGBotPath%\configs\config.json copy %PGBotPath%\configs\config.json %DownPath%
if exist %PGBotPath%\web\config\userdata.js copy %PGBotPath%\web\config\userdata.js %DownPath%
if exist %PGBotPath%\encrypt. copy %PGBotPath%\encrypt. %DownPath%
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Downloading PokemonGo-Bot--------------------
@ECHO.
@ECHO.
@ECHO.
if exist %PGBotPath% rmdir %PGBotPath% /s /q
if not exist %PGBotPath% md %PGBotPath%
cd C:\Python27\
pip2 install --upgrade virtualenv
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot %PGBotPath%
if "%OS%" == "32-BIT" pip2 install --upgrade %PGBotPath%\windows_bat\PyYAML-3.11-cp27-cp27m-win32.whl
if "%OS%" == "64-BIT" pip2 install --upgrade %PGBotPath%\windows_bat\PyYAML-3.11-cp27-cp27m-win_amd64.whl
cd %PGBotPath%
virtualenv .
call "%PGBotPath%\Scripts\activate.bat"
pip2 install --upgrade -r %PGBotPath%\requirements.txt
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Restoring Backup--------------------
@ECHO.
@ECHO.
@ECHO.
if exist %DownPath%\encrypt. COPY %DownPath%\encrypt. %PGBotPath%
if exist %DownPath%\config.json COPY %DownPath%\config.json %PGBotPath%\configs\
if exist %DownPath%\userdata.js COPY %DownPath%\userdata.js %PGBotPath%\web\config\
@ECHO.
@ECHO.
@ECHO.



:FinalInstructions
CLS
@ECHO --------------------File customization--------------------
@ECHO.
@ECHO.
@ECHO.
@ECHO Before starting the bot, please copy the following files to %PGBotPath% if you dont have them yet.
@ECHO. 
@ECHO.
@ECHO.
@ECHO ---- encrypt.so / encrypt.dll or encrypt_64.dll
@ECHO      Get them from our Slack chat! 
@ECHO      "https://pokemongo-bot.herokuapp.com/"
@ECHO. 
@ECHO.
@ECHO.
@ECHO Remember to configure both config.json and userdata.js!
@ECHO.
@ECHO.
@ECHO.
@ECHO "%PGBotPath%/configs/config.json"
@ECHO INSTRUCTIONS:
@ECHO "https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/configuration_files.md"
@ECHO.
@ECHO "%PGBotPath%/web/config/userdata.js"
@ECHO INSTRUCTIONS:
@ECHO "https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/google_map.md"
@ECHO.
@ECHO To get an Google Map API Key:
@ECHO "https://developers.google.com/maps/documentation/javascript/get-api-key"
@ECHO.
@ECHO.
@ECHO.
@PAUSE



:eof
ENDLOCAL
exit