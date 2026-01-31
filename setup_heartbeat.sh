#!/bin/bash
# Clawdbot网关心跳检测安装脚本

set -e

echo "🔧 安装Clawdbot网关心跳检测系统"

# 检查Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到python3，请先安装Python3"
    exit 1
fi

# 创建必要的目录
echo "📁 创建日志目录..."
mkdir -p ~/.clawdbot/logs

# 设置脚本权限
echo "🔐 设置脚本权限..."
chmod +x gateway_heartbeat.py

# 创建systemd服务文件
echo "🔄 创建systemd服务..."
SERVICE_FILE="/etc/systemd/system/clawdbot-heartbeat.service"

if [ -f "$SERVICE_FILE" ]; then
    echo "⚠️  服务文件已存在，备份原文件..."
    sudo cp "$SERVICE_FILE" "${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 获取当前目录
CURRENT_DIR=$(pwd)

cat << EOF | sudo tee "$SERVICE_FILE" > /dev/null
[Unit]
Description=Clawdbot Gateway Heartbeat Monitor
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $CURRENT_DIR/gateway_heartbeat.py --interval 5 --channel slack
StandardOutput=append:$HOME/.clawdbot/logs/heartbeat-service.log
StandardError=append:$HOME/.clawdbot/logs/heartbeat-service-error.log

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd服务文件创建完成"

# 创建cron任务作为备选方案
echo "⏰ 创建cron任务作为备选方案..."
CRON_JOB="*/5 * * * * cd $CURRENT_DIR && /usr/bin/python3 gateway_heartbeat.py --once --channel slack >> $HOME/.clawdbot/logs/heartbeat-cron.log 2>&1"

# 添加到crontab
(crontab -l 2>/dev/null | grep -v "gateway_heartbeat.py"; echo "$CRON_JOB") | crontab -

echo "✅ cron任务创建完成"

# 创建测试脚本
echo "🧪 创建测试脚本..."
cat > test_heartbeat.sh << 'EOF'
#!/bin/bash
echo "测试网关心跳检测..."
echo "1. 测试单次检查..."
python3 gateway_heartbeat.py --once --channel slack

echo ""
echo "2. 查看日志..."
tail -n 20 ~/.clawdbot/logs/gateway_heartbeat.log 2>/dev/null || echo "日志文件不存在"

echo ""
echo "3. 检查服务状态..."
if systemctl is-active --quiet clawdbot-heartbeat; then
    echo "✅ 心跳检测服务正在运行"
    systemctl status clawdbot-heartbeat --no-pager -l
else
    echo "⚠️  心跳检测服务未运行"
fi
EOF

chmod +x test_heartbeat.sh

# 创建管理脚本
echo "🛠️ 创建管理脚本..."
cat > manage_heartbeat.sh << 'EOF'
#!/bin/bash

case "$1" in
    start)
        echo "启动心跳检测服务..."
        sudo systemctl start clawdbot-heartbeat
        sudo systemctl enable clawdbot-heartbeat
        ;;
    stop)
        echo "停止心跳检测服务..."
        sudo systemctl stop clawdbot-heartbeat
        sudo systemctl disable clawdbot-heartbeat
        ;;
    restart)
        echo "重启心跳检测服务..."
        sudo systemctl restart clawdbot-heartbeat
        ;;
    status)
        echo "服务状态:"
        sudo systemctl status clawdbot-heartbeat --no-pager -l
        echo ""
        echo "最近日志:"
        tail -n 20 ~/.clawdbot/logs/gateway_heartbeat.log 2>/dev/null || echo "日志文件不存在"
        ;;
    logs)
        echo "查看日志:"
        tail -f ~/.clawdbot/logs/gateway_heartbeat.log
        ;;
    test)
        echo "执行单次测试..."
        python3 gateway_heartbeat.py --once --channel slack
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "命令说明:"
        echo "  start    - 启动并启用服务"
        echo "  stop     - 停止并禁用服务"
        echo "  restart  - 重启服务"
        echo "  status   - 查看服务状态和日志"
        echo "  logs     - 实时查看日志"
        echo "  test     - 执行单次测试"
        exit 1
        ;;
esac
EOF

chmod +x manage_heartbeat.sh

# 创建配置文件
echo "⚙️ 创建配置文件..."
cat > heartbeat_config.json << 'EOF'
{
    "monitor": {
        "interval_minutes": 5,
        "channel": "slack",
        "target_channel": "#initclawdbot",
        "test_message": "网关心跳检测"
    },
    "retry_settings": {
        "first_retry_wait": 30,
        "second_retry_wait": 40,
        "third_retry_wait": 50
    },
    "notifications": {
        "enable_email": false,
        "enable_slack": true,
        "enable_logging": true
    }
}
EOF

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 可用命令:"
echo "  ./manage_heartbeat.sh start    - 启动服务"
echo "  ./manage_heartbeat.sh status   - 查看状态"
echo "  ./manage_heartbeat.sh test     - 测试功能"
echo "  ./test_heartbeat.sh           - 完整测试"
echo ""
echo "📁 文件说明:"
echo "  gateway_heartbeat.py    - 主脚本"
echo "  manage_heartbeat.sh     - 管理脚本"
echo "  test_heartbeat.sh       - 测试脚本"
echo "  heartbeat_config.json   - 配置文件"
echo "  ~/.clawdbot/logs/       - 日志目录"
echo ""
echo "🔧 启动服务:"
echo "  sudo ./manage_heartbeat.sh start"
echo ""
echo "📊 查看状态:"
echo "  ./manage_heartbeat.sh status"