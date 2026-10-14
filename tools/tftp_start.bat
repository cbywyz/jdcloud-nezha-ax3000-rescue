@echo off
title Nezha Rescue - TFTP Server (192.168.10.100)
echo ============================================================
echo   Nezha AX3000 Rescue - TFTP File Server
echo   Bind IP : 192.168.10.100
echo   Board will pull kwrt-factory.bin from here
echo   *** KEEP THIS WINDOW OPEN ***
echo ============================================================
echo.
"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "C:\Users\Administrator\WorkBuddy\2026-09-03-11-17-56\nezha-flash\tftp_nezha.py"
echo.
echo Server exited.
pause
