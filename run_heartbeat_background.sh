#!/bin/bash
# 在后台运行网关心跳检测

PID_FILE="$HOME/.clawdbot/heartbeat.pid"
LOG_FILE="$HOME/.clawdbot/logs/heartbeat-background.log"

case "$1" in
    start)
        echo "启动网关心跳检测（后台模式）..."
        
        # 检查是否已经在运行
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "服务已经在运行 (PID: $PID)"
                exit 0
            else
                echo "发现旧的PID文件，但进程不存在，清理..."
                rm -f "$PID_FILE"
            fi
        fi
        
        # 创建日志目录
        mkdir -p "$(dirname "$LOG_FILE")"
        mkdir -p "$(dirname "$PID_FILE")"
        
        # 在后台运行
        nohup python3 gateway_heartbeat.py --interval 5 --channel slack >> "$LOG_FILE" 2>&1 &
        
        # 保存PID
        echo $! > "$PID_FILE"
        echo "服务已启动 (PID: $!, 日志: $LOG_FILE)"
        ;;
        
    stop)
        echo "停止网关心跳检测..."
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                echo "服务已停止 (PID: $PID)"
            else
                echo "进程不存在 (PID: $PID)"
            fi
            rm -f "$PID_FILE"
        else
            echo "PID文件不存在，尝试查找进程..."
            PIDS=$(pgrep -f "gateway_heartbeat.py")
            if [ -n "$PIDS" ]; then
                echo "找到进程: $PIDS"
                kill $PIDS
                echo "进程已终止"
            else
                echo "未找到运行中的进程"
            fi
        fi
        ;;
        
    restart)
        echo "重启网关心跳检测..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo "网关心跳检测状态:"
        
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "✅ 服务正在运行 (PID: $PID)"
                echo "   启动时间: $(ps -p "$PID" -o lstart= 2>/dev/null || echo "未知")"
                echo "   运行时间: $(ps -p "$PID" -o etime= 2>/dev/null || echo "未知")"
                
                # 显示最近日志
                echo ""
                echo "最近日志 ($LOG_FILE):"
                tail -n 10 "$LOG_FILE" 2>/dev/null || echo "   日志文件不存在或为空"
            else
                echo "❌ PID文件存在但进程未运行 (PID: $PID)"
                echo "   建议运行: $0 restart"
            fi
        else
            # 检查是否有进程在运行
            PIDS=$(pgrep -f "gateway_heartbeat.py")
            if [ -n "$PIDS" ]; then
                echo "⚠️  服务在运行但没有PID文件 (PIDs: $PIDS)"
                echo "   建议运行: $0 stop 然后 $0 start"
            else
                echo "❌ 服务未运行"
                echo "   运行: $0 start 来启动服务"
            fi
        fi
        
        # 显示心跳日志
        HEARTBEAT_LOG="$HOME/.clawdbot/logs/gateway_heartbeat.log"
        if [ -f "$HEARTBEAT_LOG" ]; then
            echo ""
            echo "心跳检测日志 ($HEARTBEAT_LOG):"
            tail -n 5 "$HEARTBEAT_LOG"
        fi
        ;;
        
    logs)
        echo "查看实时日志 (按 Ctrl+C 退出):"
        tail -f "$HOME/.clawdbot/logs/gateway_heartbeat.log" 2>/dev/null || \
        tail -f "$LOG_FILE" 2>/dev/null || \
        echo "日志文件不存在"
        ;;
        
    test)
        echo "执行单次测试..."
        python3 gateway_heartbeat.py --once --channel slack
        ;;
        
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "在容器环境中使用此脚本，因为systemd不可用"
        echo ""
        echo "命令说明:"
        echo "  start    - 在后台启动服务"
        echo "  stop     - 停止后台服务"
        echo "  restart  - 重启服务"
        echo "  status   - 查看服务状态"
        echo "  logs     - 查看实时日志"
        echo "  test     - 执行单次测试"
        exit 1
        ;;
esac