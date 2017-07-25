TITLE PokemonGo-Bot
CLS
@ECHO Off



:init
setlocal DisableDelayedExpansion
path c:\Program Files\Git\cmd;%PATH%
path C:\Python27;%PATH%
path C:\Python27\Scripts;%PATH%
SET BatPath=%~dp0
SET BotPath=%BatPath:~0,-13%
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



:startBot
CLS
ECHO.
ECHO. --------------------Verifying PokemonGo-Bot version--------------------
ECHO.
CD..
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.example') DO set OldSizeNormal=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.cluster.example') DO set OldSizeCluster=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.map.example') DO set OldSizeMap=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.optimizer.example') DO set OldSizeOptimizer=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.path.example') DO set OldSizePath=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.pokemon.example') DO set OldSizePokemon=%%~zA
git pull
pip uninstall -y pgoapi
git submodule update --init --recursive
pip install --upgrade -r requirements.txt
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.example') DO set SizeNormal=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.cluster.example') DO set SizeCluster=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.map.example') DO set SizeMap=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.optimizer.example') DO set SizeOptimizer=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.path.example') DO set SizePath=%%~zA
FOR /F "usebackq" %%A IN ('%BotPath%\configs\config.json.pokemon.example') DO set SizePokemon=%%~zA

CLS
ECHO.
ECHO. --------------------Verifying PokemonGo-Bot version--------------------
ECHO.
IF %OldSizeNormal% == %SizeNormal% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.example, check if your modifications are still valid.
ECHO.
)
IF %OldSizeCluster% == %SizeCluster% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.cluster.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.cluster.example, check if your modifications are still valid.
ECHO.
)
IF %OldSizeMap% == %SizeMap% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.map.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.map.example, check if your modifications are still valid.
ECHO.
)
IF %OldSizeOptimizer% == %SizeOptimizer% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.optimizer.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.optimizer.example, check if your modifications are still valid.
ECHO.
)
IF %OldSizePath% == %SizePath% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.path.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.path.example, check if your modifications are still valid.
ECHO.
)
IF %OldSizePokemon% == %SizePokemon% (
ECHO.
) ELSE (
ECHO. WARNING. Check your config.json if you use config.json.pokemon.example as standard config.json 
ECHO.
ECHO. Changes have been made to the config.json.pokemon.example, check if your modifications are still valid.
ECHO.
)
pause
