# 使用轻量级的 Python 3.11 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装 ffmpeg 和必要的系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 将 requirements.txt 复制到容器中
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个后端代码到容器中
COPY . .

# 暴露 Flask 运行的端口
EXPOSE 5001

# 使用 Gunicorn 运行生产环境（不要用 flask run）
# -b 0.0.0.0:5001 绑定所有 IP
# --timeout 120 增加超时时间，因为音视频处理可能需要较长时间
CMD ["gunicorn", "-b", "0.0.0.0:5001", "--workers", "1", "--threads", "8", "--timeout", "120", "app:app"]