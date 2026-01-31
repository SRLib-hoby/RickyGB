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