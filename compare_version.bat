@echo off
check_version.exe -a
check_version.exe -b
check_version.exe -c
del dllVersion.txt
del configVersion.txt
pause

