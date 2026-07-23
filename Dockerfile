FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY railway_requirements.txt ./
RUN pip install --no-cache-dir -r railway_requirements.txt

# 复制代码
COPY railway_file_server.py file_server_prod.py ./
RUN ln -sf railway_file_server.py app.py

# 创建上传目录
RUN mkdir -p /data/uploads

# 环境变量
ENV UPLOAD_DIR=/data/uploads
ENV HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

# 启动服务
# Debug: force unbuffered output to see Python errors
CMD ["python", "-u", "railway_file_server.py"]
