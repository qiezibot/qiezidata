# File Manager一键部署脚本
# 在Vultr香港服务器上执行

echo "=== 更新系统 ==="
apt update && apt upgrade -y

echo "=== 安装MySQL ==="
apt install -y mysql-server
systemctl start mysql
systemctl enable mysql

echo "=== 创建数据库 ==="
mysql -e "CREATE DATABASE IF NOT EXISTS file_manager CHARACTER SET utf8mb4;"
mysql -e "CREATE USER IF NOT EXISTS 'filemgr'@'localhost' IDENTIFIED BY 'FileMgr2024!';"
mysql -e "GRANT ALL PRIVILEGES ON file_manager.* TO 'filemgr'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

echo "=== 安装Python依赖 ==="
apt install -y python3 python3-pip python3-venv
python3 -m venv /opt/filemgr/venv
source /opt/filemgr/venv/bin/activate
pip install -r /opt/filemgr/requirements.txt

echo "=== 创建systemd服务 ==="
cat > /etc/systemd/system/filemgr.service << 'EOF'
[Unit]
Description=File Manager API
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/filemgr
Environment=DB_HOST=localhost
Environment=DB_PORT=3306
Environment=DB_USER=filemgr
Environment=DB_PASS=FileMgr2024!
Environment=DB_NAME=file_manager
Environment=UPLOAD_DIR=/opt/filemgr/uploads
Environment=HOST=0.0.0.0
Environment=PORT=8899
ExecStart=/opt/filemgr/venv/bin/python /opt/filemgr/file_server_prod.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable filemgr
systemctl start filemgr

echo ""
echo "=== 部署完成 ==="
echo "服务地址: http://$(curl -s ifconfig.me):8899"
echo "健康检查: curl http://localhost:8899/files"
