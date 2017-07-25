TITLE PokemonGo-Bot Installer
cls
@ECHO Off



:init
SETlocal DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
SET DownPathPython=https://www.python.org/ftp/python/2.7.12/
SET DownPathGit=https://github.com/git-for-windows/git/releases/download/v2.9.3.windows.1/
SET DownPathVisual=https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/
SET VisualFName=VCForPython27.msi
SET PythonFName86=python-2.7.12.msi
SET PythonFName64=python-2.7.12.amd64.msi
SET GitFName86=Git-2.9.3-32-bit.exe
SET GitFName64=Git-2.9.3-64-bit.exe
SET "batchPath=%~0"
FOR %%k in (%0) do SET batchName=%%~nk
SET log=%~dp0%batchname%.log 2>&1
SET "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
SETlocal EnableDelayedExpansion


:checkPrivileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges ) else ( goto getPrivileges )



:getPrivileges
if '%1'=='ELEV' (ECHO ELEV & shift /1 & goto gotPrivileges)
@ECHO SET UAC = CreateObject^("Shell.Application"^) > "%vbsGetPrivileges%"
@ECHO args = "ELEV " >> "%vbsGetPrivileges%"
@ECHO For Each strArg in WScript.Arguments >> "%vbsGetPrivileges%"
@ECHO args = args ^& strArg ^& " " >> "%vbsGetPrivileges%"
@ECHO Next >> "%vbsGetPrivileges%"
@ECHO UAC.ShellExecute "!batchPath!", args, "", "runas", 1 >> "%vbsGetPrivileges%"
"%SystemRoot%\System32\WScript.exe" "%vbsGetPrivileges%" %*
exit /B



:gotPrivileges
SETlocal & pushd .
cd /d %~dp0
if '%1'=='ELEV' (del "%vbsGetPrivileges%" 1>nul 2>nul & shift /1)



:detectOS
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && SET OS=32-BIT || SET OS=64-BIT

ECHO.----- Checking OS Architecture ----->%log%
ECHO.>>%log%
ECHO.The computer has "%OS%" architecture.>>%log%
ECHO.>>%log%



:CheckInstallPath
cls
call:ech
ECHO.--------------------Installation Path--------------------
call:ech
SET InstallPath=
SET /p InstallPath= "Choose an installation folder (example: C:/Test/) or press Enter to close: " ||goto:eof
ECHO.----- Input Path ----->>%log%
ECHO.>>%log%
ECHO.The input Path is "%InstallPath%">>%log%
ECHO.>>%log%
set InstallPath=%InstallPath:/=\%
ECHO.----- Converted Path ----->>%log%
ECHO.>>%log%
ECHO.The converted Path is "%InstallPath%">>%log%
ECHO.>>%log%
SET PGBotPath=%InstallPath%PokemonGo-Bot
SET DownPath=%InstallPath%Install-Files
ECHO.----- Checking Download Path ----->>%log%
ECHO.>>%log%
IF NOT EXIST %DownPath% (
ECHO.No download folder "%DownPath%"
) else (
ECHO.%DownPath% exists
)>>%log%
ECHO.>>%log%
IF NOT EXIST %DownPath% md %DownPath%
ECHO.----- Rechecking Download Path ----->>%log%
ECHO.>>%log%
IF NOT EXIST %DownPath% (
ECHO.No download folder "%DownPath%"
) else (
ECHO.%DownPath% exists
)>>%log%
ECHO.>>%log%
if %~dp0==%PGBotPath%\windows_bat\ (
COPY "%PGBotPath%\windows_bat\PokemonGo-Bot-Install.bat" %InstallPath%
CALL "%InstallPath%PokemonGo-Bot-Install.bat"
exit.
) ELSE (
ECHO.Installation Path OK^^! Proceeding^^!
)
ECHO.----- Checking Some Paths ----->>%log%
ECHO.>>%log%
ECHO.BatchPath is "%~dp0">>%log%
ECHO.PokemonGo-Bot Path is "%PGBotPath%">>%log%
ECHO.>>%log%


:Menu
cls
call:ech
ECHO.--------------------PokemonGo-Bot Installer--------------------
call:ech
if "%OS%" == "32-BIT" (
ECHO. 1 - Install 32-Bit software
) ELSE (
ECHO. 1 - Install 64-Bit software
)
ECHO.
ECHO. 2 - Install PokemonGo-Bot Master Version (Stable)
ECHO.
ECHO. 3 - Install PokemonGo-Bot Development Version (Unstable)
call:ech



:_choice
SET _ok=
SET /p _ok= Choose an option or press Enter to close: ||goto:eof
IF "%OS%" == "32-BIT" IF "%_ok%" == "1" SET CHOICE=32Bit&GOTO :32Bit
IF "%OS%" == "64-BIT" IF "%_ok%" == "1" SET CHOICE=64Bit&GOTO :64Bit
IF "%_ok%" == "2" SET CHOICE=InstallBot&GOTO :InstallBot
IF "%_ok%" == "3" SET CHOICE=InstallBot&GOTO :InstallBot
GOTO :_choice 



:32bit
ECHO.----- Checking Choice and OS ----->>%log%
ECHO.>>%log%
ECHO.Choice was "%_ok%" installing "%OS%" software>>%log%
ECHO.>>%log%
cls
call:ech
ECHO.--------------------Installation of required software--------------------
call:ech
IF NOT EXIST %DownPath%\%GitFName86% ECHO.Downloading Git...
IF NOT EXIST %DownPath%\%GitFName86% call:getit %DownPathGit% %GitFName86%
IF NOT EXIST %DownPath%\%PythonFName86% ECHO.Downloading Python...
IF NOT EXIST %DownPath%\%PythonFName86% call:getit %DownPathPython% %PythonFName86%
IF NOT EXIST %DownPath%\%VisualFName% ECHO.Downloading Visual C++ for Python...
IF NOT EXIST %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
ECHO.Installing Python...
IF EXIST %DownPath%\%PythonFName86% call:installit %PythonFName86% /quiet
ECHO.Installing Git...
IF EXIST %DownPath%\%GitFName86% call:installit %GitFName86% /SILENT
ECHO.Installing Visual C++ for Python...
IF EXIST %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
call:ech
ECHO.Installation of 32-Bit software is finished.
ECHO.
ECHO.Choose Install PokemonGo-Bot in next screen to complete installation.
call:ech
timeout /t 5
goto:Menu



:64bit
ECHO.----- Checking Choice and OS ----->>%log%
ECHO.>>%log%
ECHO.Choice was "%_ok%" installing "%OS%" software>>%log%
ECHO.>>%log%
cls
call:ech
ECHO.--------------------Installation of required software--------------------
call:ech
IF NOT EXIST %DownPath%\%GitFName64% ECHO.Downloading Git...
IF NOT EXIST %DownPath%\%GitFName64% call:getit %DownPathGit% %GitFName64%
IF NOT EXIST %DownPath%\%PythonFName64% ECHO.Downloading Python...
IF NOT EXIST %DownPath%\%PythonFName64% call:getit %DownPathPython% %PythonFName64%
IF NOT EXIST %DownPath%\%VisualFName% ECHO.Downloading Visual C++ for Python...
IF NOT EXIST %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
ECHO.Installing Python...
IF EXIST %DownPath%\%PythonFName64% call:installit %PythonFName64% /quiet
ECHO.Installing Git...
IF EXIST %DownPath%\%GitFName64% call:installit %GitFName64% /SILENT
ECHO.Installing Visual C++ for Python...
IF EXIST %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
call:ech
ECHO.Installation of 64-Bit software is finished.
ECHO.
ECHO.Choose Install PokemonGo-Bot in next screen to complete installation.
call:ech
ECHO.
timeout /t 5
goto:Menu



:getit
ECHO.----- Checking Program Downloading ----->>%log%
ECHO.>>%log%
ECHO.Downloading "%~1%~2" to "%DownPath%\%~2">>%log%
ECHO.>>%log%
start /wait powershell -Command "Invoke-WebRequest %~1%~2 -OutFile %DownPath%\%~2"
goto:eof


:installit
ECHO.----- Checking Program Installing ----->>%log%
ECHO.>>%log%
ECHO.Installing "%DownPath%\%~1 %~2">>%log%
ECHO.>>%log%
start /wait %DownPath%\%~1 %~2
goto:eof



:InstallBot
ECHO.----- Checking Choice and Bot Installing ----->>%log%
ECHO.>>%log%
ECHO.Choice was "%_ok%" installing Bot>>%log%
ECHO.>>%log%
cls
call:ech
ECHO.--------------------Creating Backup--------------------
call:ech
ECHO.----- Checking Creating Backup ----->>%log%
ECHO.>>%log%
IF EXIST %PGBotPath%\configs\auth.json (
ECHO.Copying "%PGBotPath%\configs\auth.json" to %DownPath%>>%log%
COPY %PGBotPath%\configs\auth.json %DownPath%>>%log%
) else (
ECHO.No "%PGBotPath%\configs\auth.json">>%log%
)
IF EXIST %PGBotPath%\configs\config.json (
ECHO.Copying "%PGBotPath%\configs\config.json" to %DownPath%>>%log%
COPY %PGBotPath%\configs\config.json %DownPath%>>%log%
) else (
ECHO.No "%PGBotPath%\configs\config.json">>%log%
)
IF EXIST %PGBotPath%\web\config\userdata.js (
ECHO.Copying "%PGBotPath%\web\config\userdata.js" to %DownPath%>>%log%
COPY %PGBotPath%\web\config\userdata.js %DownPath%>>%log%
) else (
ECHO.No "%PGBotPath%\web\config\userdata.js">>%log%
)
ECHO.>>%log%

cls
ECHO.
call:ech
ECHO.--------------------Downloading PokemonGo-Bot--------------------
call:ech
ECHO. Please wait... We are now downloading and installing the files for PokemonGo-Bot.
ECHO.----- Checking Removing Bot Folder ----->>%log%
ECHO.>>%log%
IF EXIST %PGBotPath% rmdir %PGBotPath% /s /q
IF EXIST %PGBotPath% (
ECHO.Problem %PGBotPath% still exists
) else (
ECHO.%PGBotPath% is removed
)>>%log%
ECHO.>>%log%
ECHO.----- Checking pip2 install or upgrade ----->>%log%
ECHO.>>%log%
pip2 install --upgrade pip>>%log%
pip2 install --upgrade virtualenv>>%log%
ECHO.>>%log%
cd C:\Python27\
ECHO.
ECHO.>>%log%
ECHO.----- Checking Clone installed ----->>%log%
ECHO.>>%log%
if "%_ok%" == "2" ECHO. Install Bot choice was Master>>%log%
if "%_ok%" == "2" git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot %PGBotPath%>>%log%
if "%_ok%" == "3" ECHO. Install Bot choice was Development>>%log%
if "%_ok%" == "3" git clone --recursive -b dev https://github.com/PokemonGoF/PokemonGo-Bot %PGBotPath%>>%log%
ECHO.>>%log%
IF EXIST %PGBotPath% ECHO.%PGBotPath% has been made>>%log%
ECHO.>>%log%
ECHO.----- Checking second pip2 install or upgrade ----->>%log%
ECHO.>>%log%
CD %PGBotPath%\
pip2 install -r requirements.txt>>%log%
ECHO.>>%log%
call:ech
ECHO.--------------------Restoring Backup--------------------
call:ech
ECHO.----- Checking Restoring Backup ----->>%log%
ECHO.>>%log%
IF EXIST %~dp0auth.json (
ECHO.Copying %~dp0auth.json to %PGBotPath%\configs\>>%log%
COPY %~dp0auth.json %PGBotPath%\configs\>>%log%
) else (
ECHO.No "%~dp0auth.json">>%log%
)
IF EXIST %~dp0config.json (
ECHO.Copying %~dp0config.json to %PGBotPath%\configs\>>%log%
COPY %~dp0config.json %PGBotPath%\configs\>>%log%
) else (
ECHO.No "%~dp0config.json">>%log%
)
IF EXIST %~dp0userdata.js (
ECHO.Copying %~dp0userdata.js to %PGBotPath%\web\config\>>%log%
COPY %~dp0userdata.js %PGBotPath%\web\config\>>%log%
) else (
ECHO.No "%~dp0userdata.js">>%log%
)
IF EXIST %DownPath%\auth.json (
ECHO.Copying %DownPath%\auth.json to %PGBotPath%\configs\>>%log%
COPY %DownPath%\auth.json %PGBotPath%\configs\>>%log%
) else (
ECHO.No "%DownPath%\auth.json">>%log%
)
IF EXIST %DownPath%\config.json (
ECHO.Copying %DownPath%\config.json to %PGBotPath%\configs\>>%log%
COPY %DownPath%\config.json %PGBotPath%\configs\>>%log%
) else (
ECHO.No "%DownPath%\config.json">>%log%
)
IF EXIST %DownPath%\userdata.js (
ECHO.Copying %DownPath%\userdata.js to %PGBotPath%\web\config\>>%log%
COPY %DownPath%\userdata.js %PGBotPath%\web\config\>>%log%
) else (
ECHO.No "%DownPath%\userdata.js">>%log%
)
ECHO.>>%Log%
ECHO. ----- End Log ----->>%log%

:FinalInstructions
cls
ECHO.--------------------File customization--------------------
call:ech
ECHO.Remember to configure auth.json, config.json and userdata.js^^!
call:ech
ECHO.BOT CONFIGURATION INSTRUCTIONS:
ECHO."https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/configuration_files.md"
call:ech
ECHO."%PGBotPath%\configs\auth.json"
ECHO."%PGBotPath%\configs\config.json"
call:ech
ECHO.MAP CONFIGURATION INSTRUCTIONS:
ECHO."https://github.com/PokemonGoF/PokemonGo-Bot/blob/master/docs/google_map.md"
call:ech
ECHO."%PGBotPath%\web\config\userdata.js"
call:ech
ECHO.TO GET A GOOGLE MAPS API KEY:
ECHO."https://developers.google.com/maps/documentation/javascript/get-api-key"
call:ech
@PAUSE

CLS
call:ech
ECHO.You can configure the auth.json and userdata.js files when you choose y in the next question.
ECHO.
ECHO.If you first want to get your Google MAPS API key choose n then 
ECHO.start PokemonGo-Bot-Configurator.bat in %PGBotPath%\windows_bat\
call:ech
SET /p json="Do you want to start the PokemonGo-Bot-Configurator (Y/N): "
IF "%json%" == "y" call %PGBotPath%\windows_bat\PokemonGo-Bot-Configurator.bat
IF "%json%" == "n" goto:eof

:ech
ECHO.
ECHO.
goto:eof

:eof
ENDLOCAL
exit