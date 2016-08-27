TITLE PokemonGo-Bot Configurator
cls
@ECHO On

:init
SETlocal DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
SET "batchPath=%~0"
FOR %%k in (%0) do SET batchName=%%~nk
SET "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
cd..
cd configs
set "testpath=%~0"
pause
SET config=config.json

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

:ConfigStart
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot Configurator--------------------
ECHO.
ECHO.
ECHO. The PokemonGo-Bot Configurator creates the needed config.json and userdata.js
ECHO.
ECHO. It only configures the needed info to start running the PokemonGo-Bot.
ECHO.
ECHO. To fine tune your config.json you will have to edit the file
ECHO.
ECHO.
ECHO.
timeout /t 10

:Menu
cls
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot Config Choice--------------------
ECHO.
ECHO.
ECHO.
ECHO. 1 - Normal config.json
ECHO.
ECHO. 2 - Cluster config.json
ECHO.
ECHO. 3 - Map config.json
ECHO.
ECHO. 4 - Optimizer config.json
ECHO.
ECHO. 5 - Path config.json
ECHO.
ECHO. 6 - Pokemon config.json
ECHO.
ECHO.
IF EXIST "config.json" (
ECHO.
ECHO.======================================================================
ECHO.=                                                                    =
ECHO.=      WARNING - Your existing config.json will be overwriten        =
ECHO.=                                                                    =
ECHO.=         Press Enter to abort or make a choice to continue          =
ECHO.=                                                                    =
ECHO.======================================================================
ECHO.
) ELSE (
ECHO.
)


:_choice
SET _ok=
SET /p _ok= Choose your config.json or press Enter to close: ||goto:eof
IF "%_ok%" == "1" SET CHOICE=Normal&GOTO :Normal
IF "%_ok%" == "2" SET CHOICE=Cluster&GOTO :Cluster
IF "%_ok%" == "3" SET CHOICE=Map&GOTO :Map
IF "%_ok%" == "4" SET CHOICE=Optimizer&GOTO :Optimizer
IF "%_ok%" == "5" SET CHOICE=Path&GOTO :Path
IF "%_ok%" == "6" SET CHOICE=Pokemon&GOTO :Pokemon
GOTO :_choice 

:Normal
call:ConfigMake config.json.example
goto:Menu

:Cluster
goto:Menu

:Map
goto:Menu

:Optimizer
goto:Menu

:Path
goto:Menu

:Pokemon
goto:Menu

:ConfigMake
cls
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot config.json creator--------------------
ECHO.
ECHO.
ECHO.{>%config%
SET /p auth_service="What AUTH SERVICE are you using ? google or ptc ?: "
ECHO.    "auth_service": "%auth_service%",>>%config%
ECHO.
Set /p YOUR_USERNAME="What's your username ?: "
ECHO.    "username": "%YOUR_USERNAME%",>>%config%
ECHO.
SET /p YOUR_PASSWORD="What's your password ?: "
ECHO.    "password": "%YOUR_PASSWORD%",>>%config%
ECHO.
SET /p SOME_LOCATION="What's the location you want to search ?: "
ECHO.    "location": "%SOME_LOCATION%",>>%config%
ECHO.
SET /p GOOGLE_API="What"s your Google Maps API Key ?: "
ECHO.    "gmapkey": "%GOOGLE_API%",>>%config%
for /F "skip=6 delims=" %%G IN ('type %~1') DO echo %%G >>%config%
goto:eof

:eof
exit