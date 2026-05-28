#!/bin/bash
set -euxo pipefail

PROJECT_DIR="/home/ec2-user/durham-aws-risk-dashboard"
REPO_URL="https://github.com/bifediora/durham-aws-risk-dashboard.git"
VENV_DIR="${PROJECT_DIR}/durham-risk-aws-env"
SERVICE_FILE="/etc/systemd/system/durham-risk-dashboard.service"
NGINX_CONF="/etc/nginx/conf.d/durham-risk-dashboard.conf"

dnf update -y
dnf install -y git python3.11 python3.11-pip python3.11-devel gcc nginx

if [ ! -d "${PROJECT_DIR}" ]; then
  git clone "${REPO_URL}" "${PROJECT_DIR}"
else
  cd "${PROJECT_DIR}"
  git pull origin main
fi

chown -R ec2-user:ec2-user "${PROJECT_DIR}"

cd "${PROJECT_DIR}"

rm -rf "${VENV_DIR}"
sudo -u ec2-user python3.11 -m venv "${VENV_DIR}"
sudo -u ec2-user "${VENV_DIR}/bin/python" -m pip install --upgrade pip
sudo -u ec2-user "${VENV_DIR}/bin/pip" install -r requirements.txt

cat > "${SERVICE_FILE}" <<'EOF'
[Unit]
Description=Durham Risk Intelligence Dashboard FastAPI Service
After=network.target

[Service]
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/durham-aws-risk-dashboard
Environment="PATH=/home/ec2-user/durham-aws-risk-dashboard/durham-risk-aws-env/bin"
ExecStart=/home/ec2-user/durham-aws-risk-dashboard/durham-risk-aws-env/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable durham-risk-dashboard
systemctl restart durham-risk-dashboard

cat > "${NGINX_CONF}" <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

nginx -t
systemctl enable nginx
systemctl restart nginx

