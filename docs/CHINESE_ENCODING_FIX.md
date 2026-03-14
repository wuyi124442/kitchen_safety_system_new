# Windows中文乱码问题解决指南

## 问题描述

在Windows系统中运行批处理文件时，可能会出现中文字符显示为乱码的问题。这通常是由于控制台代码页设置不正确导致的。

## 解决方案

### 方案1：使用修复后的脚本（推荐）

我们已经提供了多个版本的启动脚本来解决中文乱码问题：

#### 1.1 使用统一启动器
```cmd
start_django.bat
```
这个脚本会让您选择最适合的启动方式。

#### 1.2 直接使用英文版本
```cmd
run_django.bat
```
完全使用英文，避免乱码问题。

#### 1.3 使用中文版本（已修复编码）
```cmd
run_django_cn.bat
```
使用UTF-8编码的中文版本。

#### 1.4 使用PowerShell版本（最佳中文支持）
```cmd
powershell -ExecutionPolicy Bypass -File run_django.ps1
```
PowerShell对Unicode支持更好，推荐用于中文环境。

### 方案2：手动修复编码问题

#### 2.1 运行编码修复工具
```cmd
fix_chinese_encoding.bat
```

#### 2.2 手动设置代码页
在任何批处理文件开头添加：
```cmd
@echo off
chcp 65001 >nul
```

### 方案3：系统级解决方案

#### 3.1 修改控制台字体
1. 右键点击命令提示符标题栏
2. 选择"属性"
3. 在"字体"选项卡中选择支持中文的字体：
   - 新宋体
   - 微软雅黑
   - Consolas（如果安装了中文字体包）

#### 3.2 设置系统默认代码页（高级用户）
1. 按Win+R，输入`regedit`
2. 导航到：`HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage`
3. 将以下值设置为`65001`：
   - `ACP`
   - `OEMCP`
4. 重启计算机

#### 3.3 使用Windows Terminal（推荐）
Windows Terminal对Unicode支持更好：
1. 从Microsoft Store安装Windows Terminal
2. 在Windows Terminal中运行脚本

## 测试编码是否正常

运行以下命令测试中文显示：
```cmd
fix_chinese_encoding.bat
```

如果看到"厨房安全检测系统"正常显示，说明编码问题已解决。

## 各脚本说明

| 脚本文件 | 说明 | 适用场景 |
|---------|------|----------|
| `start_django.bat` | 统一启动器，可选择启动方式 | 所有用户 |
| `run_django.bat` | 英文版Django启动脚本 | 避免乱码 |
| `run_django_cn.bat` | 中文版Django启动脚本（UTF-8） | 中文环境 |
| `run_django.ps1` | PowerShell版启动脚本 | 最佳中文支持 |
| `fix_chinese_encoding.bat` | 编码问题诊断和修复 | 故障排除 |
| `activate_yolo_env.bat` | 英文版环境激活脚本 | 避免乱码 |
| `activate_yolo_env_cn.bat` | 中文版环境激活脚本（UTF-8） | 中文环境 |

## 常见问题

### Q: 为什么会出现中文乱码？
A: Windows默认使用GBK编码，而现代应用通常使用UTF-8编码，导致字符显示不正确。

### Q: 设置chcp 65001后仍有乱码怎么办？
A: 尝试更换控制台字体，或使用PowerShell版本的脚本。

### Q: 可以永久解决这个问题吗？
A: 可以通过修改注册表设置系统默认代码页，但建议使用Windows Terminal或PowerShell。

### Q: 其他应用也有中文乱码问题怎么办？
A: 这是Windows系统级问题，建议升级到Windows 10/11并使用Windows Terminal。

## 推荐使用方式

1. **新用户**：直接使用`start_django.bat`，选择PowerShell版本
2. **开发者**：使用`run_django.bat`（英文版）避免编码问题
3. **中文环境**：使用`run_django.ps1`（PowerShell版本）
4. **故障排除**：运行`fix_chinese_encoding.bat`诊断问题

## 技术原理

- **chcp 65001**：设置控制台代码页为UTF-8
- **PowerShell**：原生支持Unicode，无需额外设置
- **字体支持**：某些字体不支持中文字符显示
- **系统编码**：Windows系统默认编码与应用编码不匹配

通过以上方案，应该能够完全解决Windows环境下的中文乱码问题。