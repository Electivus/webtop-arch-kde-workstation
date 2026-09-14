@echo off
setlocal DisableDelayedExpansion
"%~dp0workstation.exe" %*
exit /b %errorlevel%
