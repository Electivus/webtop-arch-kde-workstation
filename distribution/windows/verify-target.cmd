@echo off
setlocal DisableDelayedExpansion
if "%~1"=="" goto usage
if "%~2"=="" goto usage
set "verify_image=%~1"
set "verify_report=%~f2"
set "verify_network=%~3"
if exist "%verify_report%" (
    echo Choose a new report directory; existing evidence is not overwritten. 1>&2
    exit /b 1
)
where docker >nul 2>nul
if errorlevel 1 (
    echo Docker CLI is unavailable. Start the installed Docker Desktop with Linux containers. 1>&2
    exit /b 1
)
if not exist "%~dp0setup.cmd" goto missing
if not exist "%~dp0verify-target.py" goto missing
mkdir "%verify_report%"
if errorlevel 1 exit /b 1
set "verify_stage=prerequisites"
docker version --format "{{json .Server}}" >"%verify_report%\docker-version.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
docker info --format "{{.OSType}}" >"%verify_report%\docker-os.txt" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_os="
for /f "usebackq delims=" %%O in ("%verify_report%\docker-os.txt") do set "verify_os=%%O"
if not "%verify_os%"=="linux" (
    >"%verify_report%\error.txt" echo Docker must run Linux containers.
    goto failed
)
docker info --format "{{.KernelVersion}}" >"%verify_report%\kernel.txt"
for /f "delims=" %%I in ('docker info --format "{{.ID}}"') do set "verify_engine=%%I"
set "verify_stage=extract-commands"
call "%~dp0setup.cmd" "%verify_image%" "%verify_report%\tools" >"%verify_report%\setup.txt" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
docker image inspect "%verify_image%" >"%verify_report%\image.json"
if errorlevel 1 goto failed
docker image inspect --format "{{index .Config.Labels \"io.electivus.workstation.variant\"}}" "%verify_image%" >"%verify_report%\variant.txt"
if errorlevel 1 goto failed
set "verify_variant="
for /f "usebackq delims=" %%V in ("%verify_report%\variant.txt") do set "verify_variant=%%V"
if not "%verify_variant%"=="base" if not "%verify_variant%"=="salesforce" goto failed
set "verify_name=ew-destination-%RANDOM%-%RANDOM%"
set "verify_profile=%verify_report%\profile"
set "verify_cli=%verify_report%\tools\workstation.cmd"
mkdir "%verify_report%\exchange"
>"%verify_report%\exchange\from-windows.txt" echo windows-to-linux
set "verify_stage=install"
if defined verify_network goto install_network
call "%verify_cli%" install --profile "%verify_profile%" --name "%verify_name%" --image "%verify_image%" --port 14513 --memory 6144 --cpus 4 --exchange "%verify_report%\exchange" >"%verify_report%\install.json" 2>"%verify_report%\error.txt"
goto installed
:install_network
call "%verify_cli%" install --profile "%verify_profile%" --name "%verify_name%" --image "%verify_image%" --port 14513 --memory 6144 --cpus 4 --exchange "%verify_report%\exchange" --network-config "%verify_network%" >"%verify_report%\install.json" 2>"%verify_report%\error.txt"
:installed
if errorlevel 1 goto failed
set "verify_stage=start"
call "%verify_cli%" start --profile "%verify_profile%" >"%verify_report%\start.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_stage=prepare"
call "%verify_cli%" prepare --profile "%verify_profile%" >"%verify_report%\prepare.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_stage=network"
call "%verify_cli%" network --profile "%verify_profile%" --check >"%verify_report%\network.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_stage=guest-checks"
docker cp "%~dp0verify-target.py" "%verify_name%:/config/verify-target.py" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
docker exec --user abc "%verify_name%" python3 /config/verify-target.py check --engine "%verify_engine%" --project-name "%verify_name%" --variant "%verify_variant%" >"%verify_report%\guest-checks.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_exchange="
for /f "usebackq delims=" %%L in ("%verify_report%\exchange\from-linux.txt") do set "verify_exchange=%%L"
if not "%verify_exchange%"=="linux-to-windows" goto failed
set "verify_stage=backup"
call "%verify_cli%" backup --profile "%verify_profile%" >"%verify_report%\backup.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_backup="
for /d %%B in ("%verify_profile%\backups\*") do if exist "%%~fB\manifest.sha256" set "verify_backup=%%~fB"
if not defined verify_backup goto failed
call "%verify_cli%" start --profile "%verify_profile%" >nul 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
docker exec --user abc "%verify_name%" python3 /config/verify-target.py mutate 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_stage=restore"
call "%verify_cli%" restore --profile "%verify_profile%" --backup "%verify_backup%" >"%verify_report%\restore.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
call "%verify_cli%" start --profile "%verify_profile%" >nul 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
docker exec --user abc "%verify_name%" python3 /config/verify-target.py restored >"%verify_report%\restored-project.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
set "verify_stage=stop"
call "%verify_cli%" stop --profile "%verify_profile%" >"%verify_report%\stop.json" 2>"%verify_report%\error.txt"
if errorlevel 1 goto failed
>"%verify_report%\result.txt" echo Automated checks passed. Visual desktop and physical keyboard checks remain pending.
echo Automated checks passed. Reports: "%verify_report%".
echo Next: follow docs/hyperv-verification.md for trust, shortcut, visual checks and explicit updates.
exit /b 0
:failed
>"%verify_report%\result.txt" echo FAILED at %verify_stage%. Inspect error.txt and the retained step reports.
echo Verification failed at %verify_stage%. Reports: "%verify_report%". 1>&2
echo The test profile is retained for diagnosis; unrelated installations were not stopped. 1>&2
exit /b 1
:missing
echo Keep setup.cmd, verify-target.cmd and verify-target.py together. 1>&2
exit /b 1
:usage
echo Usage: verify-target.cmd IMAGE NEW_REPORT_DIRECTORY [NETWORK_JSON] 1>&2
exit /b 1
