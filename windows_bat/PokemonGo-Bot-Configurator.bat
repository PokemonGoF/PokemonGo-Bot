TITLE PokemonGo-Bot Configurator
cls
@ECHO Off

:init
SETLOCAL DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
SET "batchPath=%~0"
FOR %%k in (%0) do SET batchName=%%~nk
SET "vbsGetPrivileges=%temp%\OEgetPriv_%batchName%.vbs"
SET BatPath=%~dp0
SET BotPath=%BatPath:~0,-13%
SET ConFigPath=%BotPath%\configs\
SET UserDataPath=%BotPath%\Web\config\
SET config=%ConFigPath%config.json
SET UserData=%UserDataPath%userdata.js
SETLOCAL EnableDelayedExpansion



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

:Warning
cls
IF EXIST "%ConFigPath%config.json" (
color C
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot Config Warning--------------------
ECHO.
ECHO.
ECHO.=============================================================================
ECHO.=                                                                           =
ECHO.= WARNING - Your existing config.json and/or userdata.js will be overwriten =
ECHO.=                                                                           =
ECHO.=     Press Enter to abort in next screen or make a choice to continue      =
ECHO.=                                                                           =
ECHO.=============================================================================
ECHO.
timeout /t 5
) ELSE (
ECHO.
)
:Menu
cls
color 7
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot Config Choice--------------------
ECHO.
ECHO. First create your config.json and then your userdata.js.
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
ECHO. 7 - userdata.js
ECHO.
ECHO.

:_choice
SET _ok=
SET /p _ok= Choose your config.json or press Enter to close: ||goto:eof
IF "%_ok%" == "1" SET CHOICE=Normal&GOTO :Normal
IF "%_ok%" == "2" SET CHOICE=Cluster&GOTO :Cluster
IF "%_ok%" == "3" SET CHOICE=Map&GOTO :Map
IF "%_ok%" == "4" SET CHOICE=Optimizer&GOTO :Optimizer
IF "%_ok%" == "5" SET CHOICE=Path&GOTO :Path
IF "%_ok%" == "6" SET CHOICE=Pokemon&GOTO :Pokemon
IF "%_ok%" == "7" SET CHOICE=UserData&GOTO :UserData
GOTO :_choice 

:Normal
call:ConfigMake %ConFigPath%config.json.example
goto:Menu

:Cluster
call:ConfigMake %ConFigPath%config.json.cluster.example
goto:Menu

:Map
call:ConfigMake %ConFigPath%config.json.map.example
goto:Menu

:Optimizer
call:ConfigMake %ConFigPath%config.json.optimizer.example
goto:Menu

:Path
call:ConfigMake %ConFigPath%config.json.path.example
goto:Menu

:Pokemon
call:ConfigMake %ConFigPath%config.json.pokemon.example
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
ECHO.    "favorite_locations":[>>%config%
ECHO.        {"name": "Milan", "coords": "45.472849,9.177567"}>>%config%
ECHO.
ECHO.Adding Favorite Locations....
ECHO.
call:morefav
ECHO.
ECHO.    ],>>%config%
SET /p GOOGLE_API="What's your Google Maps API Key ?: "
ECHO.    "gmapkey": "%GOOGLE_API%",>>%config%
ECHO.
ECHO.
FOR /F "Skip=9 usebackq delims=" %%a in (`"findstr /n ^^ %~1"`) do (
    set "myVar=%%a"
    call :processLine myVar
)
goto :eof

:processLine
SETLOCAL EnableDelayedExpansion
set "line=!%1!"
set "line=!line:*:=!"
echo(!line!>>%config%
ENDLOCAL
goto :eof

:morefav
SET _answer=
SET name=
SET coords=
ECHO.
SET /p _answer="Do you want to add more favorite locations (Y/N) ?: "
IF "%_answer%" == "y" goto :favorite
IF "%_answer%" == "n" goto :eof
:favorite
ECHO.
ECHO.
SET /p name="What City do you want to add ?: "
SET /p coords="What coordinates has that City ? (example: 45.472849,9.177567 ): "
ECHO.        {"name": "%name%", "coords": "%coords%"}>>%config%
goto:morefav

:UserData
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot userdata.js creator--------------------
ECHO.
ECHO.
ECHO.// MUST CONFIGURE THE USER ARRAY AND GOOGLE MAPS API KEY.>%UserData%
ECHO.// YOU CAN GET A KEY HERE: https://developers.google.com/maps/documentation/javascript/get-api-key>>%UserData%
ECHO.var userInfo = {>>%UserData%
Set /p users="What's the username to use ?: "
ECHO.	users: ["%users%"],>>%UserData%
ECHO.	userZoom: true,>>%UserData%
ECHO.	zoom: 16,>>%UserData%
ECHO.	userFollow: true,>>%UserData%
SET /p API="What's your Google Maps API Key ?: "
ECHO.	gMapsAPIKey: "%API%",>>%UserData%
ECHO.	botPath: true,>>%UserData%
ECHO.	actionsEnabled: false>>%UserData%
ECHO.};>>%UserData%
call:EndUserData
goto:eof

:EndUserData
cls
ECHO.
ECHO.
ECHO.Your %config% and %UserData% has been made.
ECHO.
ECHO.If you want to customize your %config% then you have to edit him.
ECHO.
ECHO.After that you are ready to start the bot.
ECHO.
ECHO.
timeout /t 10
goto:eof

:eof
exit