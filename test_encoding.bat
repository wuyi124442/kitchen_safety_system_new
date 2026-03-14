@echo off
REM 测试中文编码是否正常工作

echo Testing without encoding fix:
echo 厨房安全检测系统
echo Kitchen Safety Detection System
echo.

echo Setting UTF-8 encoding...
chcp 65001 >nul

echo Testing with UTF-8 encoding:
echo 厨房安全检测系统
echo Kitchen Safety Detection System
echo.

echo If Chinese characters display correctly above, encoding is working.
echo 如果上面的中文字符显示正常，说明编码工作正常。

pause