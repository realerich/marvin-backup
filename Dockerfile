# Dockerfile for Marvin/OpenClaw Environment
# 基于 Ubuntu 22.04

FROM ubuntu:22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
ENV NODE_VERSION=22
ENV PYTHON_VERSION=3.12

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    tzdata \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# 安装 OpenClaw
RUN npm install -g openclaw

# 创建工作目录
WORKDIR /root/.openclaw/workspace

# 复制 requirements.txt
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# 复制初始化脚本
COPY tools/init_github_core.sh /tmp/init_github_core.sh
RUN chmod +x /tmp/init_github_core.sh

# 创建必要的目录
RUN mkdir -p /root/.openclaw/workspace/config \
    /root/.openclaw/workspace/tools \
    /root/.openclaw/workspace/memory \
    /root/.openclaw/workspace/data \
    /root/.openclaw/workspace/logs

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 暴露端口（如果需要）
EXPOSE 3000 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD openclaw status || exit 1

# 启动命令
CMD ["/bin/bash", "-c", "echo 'Marvin environment ready' && tail -f /dev/null"]