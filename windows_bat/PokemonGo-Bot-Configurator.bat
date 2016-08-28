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
SET AuthPath=%BotPath%\configs\
SET UserDataPath=%BotPath%\Web\config\
SET auth=%AuthPath%auth.json
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
ECHO. The PokemonGo-Bot Configurator creates the needed %AuthPath%auth.json and %UserDataPath%userdata.js
ECHO.
ECHO. It only configures the needed info to login with the PokemonGo-Bot.
ECHO.
ECHO. Choose one of the %AuthPath%config.json.examples and rename it to %AuthPath%config.json
ECHO.
ECHO. To fine tune your %AuthPath%config.json you will have to edit the file.
ECHO.
ECHO.
ECHO.
timeout /t 10

:Warning
cls
IF EXIST "%AuthPath%auth.json" (
color C
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot Config Warning--------------------
ECHO.
ECHO.
ECHO.=============================================================================
ECHO.=                                                                           =
ECHO.=  WARNING - Your existing auth.json and/or userdata.js will be overwriten  =
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
ECHO.--------------------PokemonGo-Bot Auth/Userdata Creator--------------------
ECHO.
ECHO. First create your %AuthPath%auth.json and then your %UserDataPath%userdata.js.
ECHO.
ECHO. 1 - %AuthPath%auth.json
ECHO.
ECHO. 2 - %UserDataPath%userdata.js
ECHO.
ECHO.

:_choice
SET _ok=
SET /p _ok= Make your choice or press Enter to close: ||goto:eof
IF "%_ok%" == "1" SET CHOICE=Auth&GOTO :Auth
IF "%_ok%" == "2" SET CHOICE=UserData&GOTO :UserData
GOTO :_choice 

:Auth
call:AuthMake %AuthPath%auth.json.example
goto:Menu

:AuthMake
cls
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot auth.json creator--------------------
ECHO.
ECHO.
ECHO.{>%auth%
SET /p auth_service="What AUTH SERVICE are you using ? google or ptc ?: "
ECHO.    "auth_service": "%auth_service%",>>%auth%
ECHO.
Set /p YOUR_USERNAME="What's your username ?: "
ECHO.    "username": "%YOUR_USERNAME%",>>%auth%
ECHO.
SET /p YOUR_PASSWORD="What's your password ?: "
ECHO.    "password": "%YOUR_PASSWORD%",>>%auth%
ECHO.
SET /p SOME_LOCATION="What's the location you want to search ?: "
ECHO.    "location": "%SOME_LOCATION%",>>%auth%
ECHO.
ECHO.    "favorite_locations":[>>%auth%
ECHO.        {"name": "Milan", "coords": "45.472849,9.177567"}>>%auth%
ECHO.
ECHO.Adding Favorite Locations....
ECHO.
call:morefav
ECHO.
ECHO.    ],>>%auth%
SET /p GOOGLE_API="What's your Google Maps API Key ?: "
ECHO.    "gmapkey": "%GOOGLE_API%",>>%auth%
ECHO.
ECHO.    "encrypt_location": "",>>%auth%
SET /p telegram="What's your telegram token? Enter for leave blank: "
ECHO.    "telegram_token": "%telegram%">>%auth%
ECHO.)>>%auth%
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
ECHO.        {"name": "%name%", "coords": "%coords%"}>>%auth%
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
ECHO.Your %auth% and %UserData% has been made.
ECHO.
ECHO.Choose one of the %AuthPath%config.json.examples and rename it to %AuthPath%config.json
ECHO.
ECHO.If you want to customize your %AuthPath%config.json then you have to edit him.
ECHO.
ECHO.After that you are ready to start the bot.
ECHO.
ECHO.
timeout /t 10
goto:eof

:eof
exit