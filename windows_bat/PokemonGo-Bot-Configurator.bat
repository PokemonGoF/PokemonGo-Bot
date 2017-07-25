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
ECHO. The PokemonGo-Bot Configurator creates
ECHO.
ECHO. %AuthPath%auth.json
ECHO.
ECHO. and %UserDataPath%userdata.js
ECHO.
ECHO. It only configures the needed info to login with the PokemonGo-Bot.
ECHO.
ECHO. Choose one of the %AuthPath%config.json.examples
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
ECHO.=           WARNING - Your existing auth.json, userdata.js and              =
ECHO.=                                                                           =
ECHO.=                    config.json will be overwriten.                        =
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
ECHO.
ECHO. 1 - %AuthPath%auth.json
ECHO.
ECHO. 2 - %UserDataPath%userdata.js
ECHO.
ECHO. 3 - Choose a config.json
ECHO.
ECHO.
ECHO.
ECHO. First create your %AuthPath%auth.json
ECHO.
ECHO. then your %UserDataPath%userdata.js
ECHO.
ECHO. after that choose 3 to choose your config.json.
ECHO.
ECHO.

:_choice
SET _ok=
SET /p _ok= Make your choice or press Enter to close: ||goto:eof
IF "%_ok%" == "1" SET CHOICE=Auth&GOTO :Auth
IF "%_ok%" == "2" SET CHOICE=UserData&GOTO :UserData
IF "%_ok%" == "3" SET CHOICE=Menu2&GOTO :Menu2
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
ECHO.
ECHO.Adding Favorite Locations....
ECHO.
call:morefav
ECHO.
ECHO.    ],>>%auth%
SET /p GOOGLE_API="What's your Google Maps API Key ?: "
ECHO.    "gmapkey": "%GOOGLE_API%",>>%auth%
ECHO.
SET /p hashkey="What's your Hashing Server Key ?: "
ECHO.    "hashkey": "%hashkey%",>>%auth%
ECHO.
SET /p telegram="What's your telegram token? Enter for leave blank: "
ECHO.    "telegram_token": "%telegram%">>%auth%
ECHO.}>>%auth%
goto :eof


:morefav
ECHO.
SET /p _answer="Do you want to add a favorite location (Y/N)?: "
IF "%_answer%" == "y" goto :choice1
IF "%_answer%" == "n" goto :eof
:choice1
ECHO.
ECHO.
SET /p name="What City do you want to add ?: "
SET /p coords="What coordinates has that City ? (example: 45.472849,9.177567 ): "
ECHO.
ECHO.
:choice2
ECHO.
ECHO.
SET /p _answer2="Do you want to add more favorite locations (Y/N)?: "
IF "%_answer2%" == "y" ECHO.        {"name": "%name%", "coords": "%coords%"},>>%auth%&goto :favorite
IF "%_answer2%" == "n" ECHO.        {"name": "%name%", "coords": "%coords%"}>>%auth%&goto :eof
:favorite
SET _answer2=
SET name=
SET coords=
ECHO.
ECHO.
SET /p name="What City do you want to add ?: "
SET /p coords="What coordinates has that City ? (example: 45.472849,9.177567 ): "
goto:choice2

:UserData
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot userdata.js creator--------------------
ECHO.
ECHO.
ECHO.// MUST CONFIGURE THE USER ARRAY AND GOOGLE MAPS API KEY.>%UserData%
ECHO.// YOU CAN GET A KEY HERE: https://developers.google.com/maps/documentation/javascript/get-api-key>>%UserData%
ECHO.var userInfo = {>>%UserData%
ECHO. 	users: [{>>%UserData%
ECHO. 	    enable: true,>>%UserData%
Set /p users="What's the username to use ?: "
ECHO. 	    username: "%users%",>>%UserData%
ECHO. 	    socketAddress: "127.0.0.1:4000",>>%UserData%
ECHO. 	    enableSocket: true>>%UserData%
ECHO. 	}],>>%UserData%
ECHO. 	userZoom: false,>>%UserData%
ECHO. 	userPath: true,>>%UserData%
ECHO. 	zoom: 16,>>%UserData%
ECHO. 	userFollow: true,>>%UserData%
SET /p API="What's your Google Maps API Key ?: "
ECHO. 	gMapsAPIKey: "%API%">>%UserData%
ECHO. };>>%UserData%
goto:menu

:Menu2
cls
ECHO.
ECHO.
ECHO.--------------------PokemonGo-Bot config.json chooser--------------------
ECHO.
ECHO. 
ECHO. 1 - config.json.example
ECHO.
ECHO. 2 - config.json.cluster.example
ECHO.
ECHO. 3 - config.json.map.example
ECHO.
ECHO. 4 - config.json.optimizer.example
ECHO.
ECHO. 5 - config.json.path.example
ECHO.
ECHO. 6 - config.json.pokemon.example
ECHO.
ECHO. Choose the config you want to use with your bot,
ECHO.
ECHO. to customize it you will have to edit %AuthPath%config.json.
ECHO.
ECHO.
:_choice2
SET _ok2=
SET /p _ok2= Make your choice or press Enter to close: ||goto:eof
IF "%_ok2%" == "1" copy %AuthPath%config.json.example %AuthPath%config.json
IF "%_ok2%" == "2" copy %AuthPath%config.json.cluster.example %AuthPath%config.json
IF "%_ok2%" == "3" copy %AuthPath%config.json.map.example %AuthPath%config.json
IF "%_ok2%" == "4" copy %AuthPath%config.json.optimizer.example %AuthPath%config.json
IF "%_ok2%" == "5" copy %AuthPath%config.json.path.example %AuthPath%config.json
IF "%_ok2%" == "6" copy %AuthPath%config.json.pokemon.example %AuthPath%config.json
GOTO :EndUserData 

:EndUserData
cls
ECHO.
ECHO.
ECHO. Your %auth% and %UserData% have been made.
ECHO.
ECHO. %AuthPath%config.json needs to be customized
ECHO.
ECHO. or you can run the bot with the default values.
ECHO.
ECHO. After that you are ready to start the bot.
ECHO.
ECHO.
timeout /t 10
goto:eof

:eof
exit