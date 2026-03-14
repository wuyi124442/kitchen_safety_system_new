# 厨房安全检测系统启动指南

## 快速启动

### Windows用户

#### 方法1：使用统一启动器（推荐）
```cmd
start_django.bat
```
这个脚本会显示菜单，让您选择最适合的启动方式。

#### 方法2：根据需要选择特定版本
- **英文版本**（避免乱码）：`run_django.bat`
- **中文版本**（UTF-8编码）：`run_django_cn.bat`
- **PowerShell版本**（最佳中文支持）：`run_django.ps1`

#### 方法3：如遇到中文乱码问题
```cmd
fix_chinese_encoding.bat
```

### Linux/Mac用户
```bash
./run_django.sh
```

## 环境准备

### 1. 激活conda环境

#### Windows
```cmd
# 英文版本
activate_yolo_env.bat

# 中文版本
activate_yolo_env_cn.bat
```

#### Linux/Mac
```bash
source activate_yolo_env.sh
```

### 2. 手动激活（如果脚本失败）
```bash
conda activate yolo
```

## 访问系统

启动成功后，在浏览器中访问：

- **Web界面**: http://127.0.0.1:8000
- **管理后台**: http://127.0.0.1:8000/admin
- **默认管理员账户**: admin / admin123

## 中文乱码解决方案

### 问题症状
- 批处理文件中的中文显示为乱码
- 控制台输出中文字符异常

### 解决步骤

1. **使用PowerShell版本**（推荐）
   ```cmd
   powershell -ExecutionPolicy Bypass -File run_django.ps1
   ```

2. **运行编码修复工具**
   ```cmd
   fix_chinese_encoding.bat
   ```

3. **手动设置编码**
   在命令提示符中运行：
   ```cmd
   chcp 65001
   ```

4. **更换控制台字体**
   - 右键点击命令提示符标题栏
   - 选择"属性" > "字体"
   - 选择支持中文的字体（如新宋体、微软雅黑）

### 各版本说明

| 脚本 | 特点 | 适用场景 |
|------|------|----------|
| `start_django.bat` | 统一启动器 | 所有用户 |
| `run_django.bat` | 英文版本 | 避免乱码 |
| `run_django_cn.bat` | 中文版本 | 中文环境 |
| `run_django_robust.bat` | 健壮版本 | 解决路径问题 |
| `run_django_no_redis.bat` | 无Redis版本 | 解决Redis错误 |
| `run_django.ps1` | PowerShell版本 | 最佳中文支持 |
| `diagnose_django_issue.bat` | 诊断工具 | 故障排除 |

## 常见问题

### Q: conda命令找不到
A: 确保已安装Anaconda或Miniconda，并重启命令提示符。

### Q: yolo环境不存在
A: 运行 `activate_yolo_env.bat` 自动创建环境。

### Q: 端口8000被占用
A: 修改启动脚本中的端口号，或关闭占用端口的程序。

### Q: 中文仍然乱码
A: 使用PowerShell版本：`run_django.ps1`

### Q: simple_django_start.py文件不存在
A: 
1. 确保在项目根目录中运行脚本
2. 运行诊断工具：`diagnose_django_issue.bat`
3. 使用健壮版本：`run_django_robust.bat`

### Q: Redis连接错误
A: 
1. 使用无Redis模式：`run_django_no_redis.bat`
2. 或在统一启动器中选择"No Redis version"
3. 详细解决方案请查看：`docs/REDIS_ISSUE_FIX.md`

### Q: 脚本运行失败
A: 按以下顺序尝试：
1. `run_django_no_redis.bat` - 无Redis模式（推荐）
2. `run_django_robust.bat` - 健壮版本
3. `run_django.ps1` - PowerShell版本
4. `diagnose_django_issue.bat` - 诊断问题

## 系统要求

- Python 3.9+
- Anaconda或Miniconda
- Windows 10/11（Windows用户）
- 至少4GB内存
- 支持中文的字体（Windows用户）

## 技术支持

如遇到问题，请：
1. 查看 `docs/CHINESE_ENCODING_FIX.md` 详细解决方案
2. 运行 `check_conda_env.py` 检查环境配置
3. 查看系统日志文件

---

**提示**: 首次启动可能需要较长时间来下载和安装依赖包，请耐心等待。