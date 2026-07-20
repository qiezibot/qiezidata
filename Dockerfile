FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY file_server_prod.py .

# 创建上传目录
RUN mkdir -p /data/uploads

# 环境变量
ENV DB_HOST=localhost
ENV DB_PORT=3306
ENV DB_USER=root
ENV DB_PASS=
ENV DB_NAME=file_manager
ENV UPLOAD_DIR=/data/uploads
ENV HOST=0.0.0.0
ENV PORT=8899

EXPOSE 8899

CMD ["python", "file_server_prod.py"]
