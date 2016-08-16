TITLE PokemonGo-Bot Installer
@ECHO OFF
CLS
:init
setlocal DisableDelayedExpansion
set PGBotPath=c:\Python27\PokemonGo-Bot
set DownPath=c:\PGBot
if not exist %DownPath% md %DownPath%
set DownPathUnzip=http://www2.cs.uidaho.edu/~jeffery/win32/
set UnzipFname=unzip.exe
set DownPathPython=https://www.python.org/ftp/python/2.7.12/
set DownPathGit=https://github.com/git-for-windows/git/releases/download/v2.9.3.windows.1/
set DownPathProtoc=https://github.com/google/protobuf/releases/download/v3.0.0-beta-4/
set ProtocFname=protoc-3.0.0-beta-4-win32.zip
set DownPathVisual=https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/
Set VisualFName=VCForPython27.msi
set "batchPath=%~0"
for %%k in (%0) do set batchName=%%~nk
set "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
setlocal EnableDelayedExpansion

:checkSomeThings
if exist %PGBotPath%\configs\config.json copy %PGBotPath%\configs\config.json %DownPath%
if exist %PGBotPath%\web\config\userdata.js copy %PGBotPath%\web\config\userdata.js %DownPath%
if exist %PGBotPath%\encrypt. copy %PGBotPath%\encrypt. %DownPath%
reg Query "HKLM\Hardware\Description\System\CentralProcessor\0" | find /i "x86" > NUL && set OS=32-BIT || set OS=64-BIT

:checkPrivileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges ) else ( goto getPrivileges )

:getPrivileges
if '%1'=='ELEV' (echo ELEV & shift /1 & goto gotPrivileges)
ECHO.
ECHO Set UAC = CreateObject^("Shell.Application"^) > "%vbsGetPrivileges%"
ECHO args = "ELEV " >> "%vbsGetPrivileges%"
ECHO For Each strArg in WScript.Arguments >> "%vbsGetPrivileges%"
ECHO args = args ^& strArg ^& " " >> "%vbsGetPrivileges%"
ECHO Next >> "%vbsGetPrivileges%"
ECHO UAC.ShellExecute "!batchPath!", args, "", "runas", 1 >> "%vbsGetPrivileges%"
"%SystemRoot%\System32\WScript.exe" "%vbsGetPrivileges%" %*
exit /B

:gotPrivileges
setlocal & pushd .
cd /d %~dp0
if '%1'=='ELEV' (del "%vbsGetPrivileges%" 1>nul 2>nul & shift /1)
call:ech
@ECHO --------------------PokemonGo-Bot Installer--------------------
call:ech
@ECHO. Before we can install PokemonGo-Bot, you need to have the following programs and tools installed.
call:ech
@ECHO. All needed files will be downloaded or copied to the folder %DownPath%.
call:ech
@ECHO. - Python 2.7.x
call:ech
@ECHO. - git
call:ech
@ECHO. - Protoc
call:ech
@ECHO. - Microsoft Visual C++ Compiler for Python 2.7
call:ech
@ECHO. - encrypt.so and encrypt.dll or encrypt_64.dll
call:ech
@ECHO. - If you already have a config.json and a userdata.js, files will be copied to the folder %DownPath%.
call:ech
ECHO. Wait 10 seconds or press any key to continue...
timeout /t 10 >nul
:Menu
CLS
ECHO.
ECHO.--------------------PokemonGo-Bot Installer Menu---------------
ECHO.
ECHO.
if "%OS%" == "32-BIT" (
	ECHO. 1 Install 32-Bit Programs
	) ELSE (
	ECHO. 1 Install 64-Bit Programs
	)
ECHO. 2 Install PokemonGo-Bot
ECHO.
ECHO. You have a %OS% System. Best for you is to install %OS% Programs.
ECHO.
ECHO.
:_choice
set _ok=
set /p _ok= Make a choice or Return to close: ||goto:eof
if "%OS%" == "32-BIT" IF "%_ok%" == "1" SET CHOICE=32Bit&GOTO :32Bit
if "%OS%" == "64-BIT" IF "%_ok%" == "1" SET CHOICE=64Bit&GOTO :64Bit
IF "%_ok%" == "2" SET CHOICE=GoBot&GOTO :GoBot
GOTO :_choice 
:32bit
set PythonFName86=python-2.7.12.msi
set GitFName86=Git-2.9.3-32-bit.exe
if not exist %DownPath%\unzip.exe call:getit %DownPathUnzip% %UnzipFName%
if not exist %DownPath%\%PythonFName86% call:getit %DownPathPython% %PythonFName86%
if exist %DownPath%\%PythonFName86% call:installit %PythonFName86% /quiet
if not exist %DownPath%\%GitFName86% call:getit %DownPathGit% %GitFName86%
if exist %DownPath%\%GitFName86% call:installit %GitFName86% /SILENT
if not exist %DownPath%\%ProtocFName% call:getit %DownPathProtoc% %ProtocFName%
if exist %DownPath%\%ProtocFName% call:extractit %DownPath% %ProtocFName%
if not exist %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
if exist %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
cls
call:ech
ECHO. Install 32-Bit Programs have finished
ECHO. Choose Install PokemonGo-Bot in next screen to complete.
call:ech
ECHO. Wait 5 seconds or press any key to continue...
timeout /t 5 >nul
goto:Menu
:64bit
set PythonFName64=python-2.7.12.amd64.msi
set GitFName64=Git-2.9.3-64-bit.exe
if not exist %DownPath%\unzip.exe call:getit %DownPathUnzip% %UnzipFName%
if not exist %DownPath%\%PythonFName64% call:getit %DownPathPython% %PythonFName64%
if exist %DownPath%\%PythonFName64% call:installit %PythonFName64% /quiet
if not exist %DownPath%\%GitFName64% call:getit %DownPathGit% %GitFName64%
if exist %DownPath%\%GitFName64% call:installit %GitFName64% /SILENT
if not exist %DownPath%\%ProtocFName% call:getit %DownPathProtoc% %ProtocFName%
if exist %DownPath%\%ProtocFName% call:extractit %DownPath% %ProtocFName%
if not exist %DownPath%\%VisualFName% call:getit %DownPathVisual% %VisualFName%
if exist %DownPath%\%VisualFName% call:installit %VisualFName% /quiet
cls
call:ech
ECHO. Install 64-Bit Programs have finished
ECHO. Choose Install PokemonGo-Bot in next screen to complete.
call:ech
ECHO. Wait 5 seconds or press any key to continue...
timeout /t 5 >nul
goto:Menu
:ech
@ECHO.
@ECHO.
goto:eof
:getit
start /wait powershell -Command "Invoke-WebRequest %~1%~2 -OutFile %DownPath%\%~2"
goto:eof
:installit
start /wait %DownPath%\%~1 %~2
goto:eof
:extractit
start /wait %DownPath%\unzip.exe -o %DownPath%\%ProtocFName% bin\protoc.exe -d %DownPath%\
if exist %DownPath%\bin\protoc.exe copy %DownPath%\bin\protoc.exe c:\Python27\Scripts
goto:eof
:GoBot
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Downloading and installing PokemonGo-Bot--------------------
@ECHO.
@ECHO.
@ECHO.
@ECHO.
if exist %PGBotPath% RMDIR %PGBotPath% /s /q
cd C:\Python27\
pip2 install --upgrade pip
pip2 install --upgrade virtualenv
git clone --recursive -b master https://github.com/PokemonGoF/PokemonGo-Bot
if "%OS%" == "32-BIT" pip2 install --upgrade "%PGBotPath%\windows_bat\PyYAML-3.11-cp27-cp27m-win32.whl"
if "%OS%" == "64-BIT" pip2 install --upgrade "%PGBotPath%\windows_bat\PyYAML-3.11-cp27-cp27m-win_amd64.whl"
pip2 install --upgrade -r %PGBotPath%\requirements.txt
cd %PGBotPath%
virtualenv .
call %PGBotPath%\Scripts\activate.bat
pip2 install --upgrade -r %PGBotPath%\requirements.txt
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------Copying additional files--------------------
@ECHO.
@ECHO.
@ECHO.
if exist %DownPath%\encrypt. COPY %DownPath%\encrypt. %PGBotPath%
if exist %DownPath%\config.json COPY %DownPath%\config.json %PGBotPath%\configs\
if exist %DownPath%\userdata.js COPY %DownPath%\userdata.js %PGBotPath%\web\config\
@ECHO.
@ECHO.
@ECHO.
@ECHO --------------------File customization--------------------
@ECHO.
@ECHO.
@ECHO.
@ECHO Remember to configure both config.json and userdata.js!
@ECHO.
@ECHO %PGBotPath%\configs\config.json
@ECHO.
@ECHO %PGBotPath%\web\config\userdata.js
@ECHO.
@ECHO To get an Google Map API Key:
@ECHO https://developers.google.com/maps/documentation/javascript/get-api-key
@ECHO.
@ECHO.
@ECHO.
pause
:eof
ENDLOCAL
exit
