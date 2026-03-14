# 厨房安全检测系统 Docker 镜像
# 多阶段构建优化镜像大小

FROM python:3.10-slim as base

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgthread-2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 复制依赖文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# 创建非root用户
RUN groupadd -r kitchen && useradd -r -g kitchen -d /app -s /bin/bash kitchen

# 复制项目文件
COPY --chown=kitchen:kitchen . .

# 创建必要的目录并设置权限
RUN mkdir -p logs config models data && \
    chown -R kitchen:kitchen /app && \
    chmod +x kitchen_safety_system/main.py && \
    chmod -R 755 /app

# 切换到非root用户
USER kitchen

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python scripts/health-check.py || exit 1

# 添加启动脚本
COPY --chown=kitchen:kitchen scripts/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# 启动命令
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["start"]