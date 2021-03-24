@echo off 

set HOME=%HOMEDRIVE%\%HOMEPATH%
Rem Directory of the check-assignments repo
set CHECK_ASSIGNMENTS_DIR=%HOME%\Documents\check-assignments

Rem Directory of the write-your-python-program repo
Rem (only needed when checking python code, just leave as is if not needed)
set WYPP_DIR=%HOME%\Documents\write-your-python-program

Rem Gradle executable (only needed when checking java code, just leave as is if not needed)
set GRADLE=C:\Gradle\gradle-6.8.3\bin\gradle.bat

Rem Python 3 executable
set PYTHON=python

%PYTHON% %CHECK_ASSIGNMENTS_DIR%/src/check.py --wypp %WYPP_DIR% --gradle %GRADLE% %*