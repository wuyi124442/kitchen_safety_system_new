@echo off
REM 中文编码问题修复脚本
REM 设置控制台代码页为UTF-8以支持中文显示
chcp 65001 >nul

echo ========================================
echo 中文编码问题修复工具
echo ========================================
echo.

echo 当前系统信息:
echo 代码页: %CODEPAGE%
echo 系统语言: %LANG%
echo.

echo 正在设置UTF-8编码...
chcp 65001

echo.
echo 测试中文显示:
echo 厨房安全检测系统
echo Kitchen Safety Detection System
echo.

echo 如果上面的中文显示正常，说明编码问题已解决。
echo 如果仍有乱码，请尝试以下解决方案:
echo.
echo 1. 右键点击命令提示符标题栏 ^> 属性 ^> 字体
echo    选择支持中文的字体，如"新宋体"或"微软雅黑"
echo.
echo 2. 在注册表中设置默认代码页:
echo    HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage
echo    将 ACP 和 OEMCP 设置为 65001
echo.
echo 3. 使用PowerShell替代CMD:
echo    PowerShell对Unicode支持更好
echo.

pause