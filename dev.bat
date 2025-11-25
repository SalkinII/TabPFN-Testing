@echo off
REM Batch wrapper for dev.ps1 to bypass PowerShell execution policy
powershell -ExecutionPolicy Bypass -File "%~dp0dev.ps1" %*


