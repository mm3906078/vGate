#!/bin/bash
apt update
apt install -y python3-pip python3
pip3 install pytz
modprobe iptable_nat
echo 1 > /proc/sys/net/ipv4/ip_forward
touch /etc/systemd/system/vgate.service
cat > /etc/systemd/system/vgate.service <<'EOF'
[Unit]
Description=Virtual Gate
After=multi-user.target
[Service]
Type=simple
Restart=always
ExecStart=/bin/bash -c 'cd /opt/vGate/ && python3 main.py'
RestartSec=1
StartLimitInterval=0
[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
