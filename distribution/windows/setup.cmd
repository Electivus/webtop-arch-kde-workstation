@echo off
setlocal DisableDelayedExpansion
set "workstation_image=%~1"
if not defined workstation_image set "workstation_image=electivus/webtop-arch-kde-base:stable"
set "workstation_bundle=%~2"
if not defined workstation_bundle set "workstation_bundle=%CD%\workstation-tools"
if exist "%workstation_bundle%\workstation.exe" (
    echo Choose an empty destination directory. 1>&2
    exit /b 1
)
if exist "%workstation_bundle%\workstation.cmd" (
    echo Choose an empty destination directory. 1>&2
    exit /b 1
)
if not exist "%workstation_bundle%\." mkdir "%workstation_bundle%"
if errorlevel 1 exit /b 1
set "workstation_extract=ew-extract-%RANDOM%-%RANDOM%"
docker create --name "%workstation_extract%" --entrypoint /bin/true "%workstation_image%" >nul
if errorlevel 1 exit /b 1
docker cp "%workstation_extract%:/opt/electivus/windows/." "%workstation_bundle%"
set "workstation_result=%errorlevel%"
docker rm -v "%workstation_extract%" >nul
if not "%workstation_result%"=="0" exit /b %workstation_result%
if errorlevel 1 exit /b 1
echo Commands extracted to "%workstation_bundle%".
exit /b 0
