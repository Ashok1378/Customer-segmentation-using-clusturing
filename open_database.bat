@echo off
title MySQL Database - Customer Segmentation
echo ============================================================
echo   Opening MySQL Database: customer_segmentation
echo ============================================================
echo.

"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -proot -D customer_segmentation

if %errorlevel% neq 0 (
    echo.
    echo Could not connect with default password 'root'.
    echo Trying manual password prompt...
    "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p -D customer_segmentation
)
pause
