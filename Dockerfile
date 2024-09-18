# 使用一个轻量级的 Python 基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制你的 Python 文件到容器中
COPY . /app

# 安装依赖库
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && pip install --no-cache-dir flask opencv-python numpy pyotp pyzbar Pillow sqlite3

# 暴露 Flask 的默认端口
EXPOSE 2063

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 启动 Flask 应用
CMD ["flask", "run"]
