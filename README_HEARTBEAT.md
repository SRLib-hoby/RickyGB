# Clawdbot网关心跳检测系统

## 🎯 概述

这是一个用于监控Clawdbot网关活跃状态的心跳检测系统。当使用GitHub Codespace时，Clawdbot网关可能会偶尔自动停止，此系统可以自动检测并重启网关。

## 📋 功能特点

### 核心功能
- ✅ **定时心跳检测** - 每5分钟发送测试消息
- ✅ **三级重试机制** - 30s → 40s → 50s 逐步重试
- ✅ **自动重启网关** - 所有重试失败后自动重启
- ✅ **详细日志记录** - 完整的操作日志和错误日志

### 检测逻辑
1. **每5分钟**发送一条测试消息到AI
2. **等待30秒**，如果没有响应 → 发送第二次
3. **再等待40秒**，如果没有响应 → 发送第三次
4. **再等待50秒**，如果没有响应 → 重启网关

## 🚀 快速开始

### 安装
```bash
# 1. 设置脚本权限
chmod +x setup_heartbeat.sh

# 2. 运行安装脚本
./setup_heartbeat.sh

# 3. 启动服务
sudo ./manage_heartbeat.sh start
```

### 基本使用
```bash
# 查看服务状态
./manage_heartbeat.sh status

# 执行单次测试
./manage_heartbeat.sh test

# 查看实时日志
./manage_heartbeat.sh logs

# 停止服务
sudo ./manage_heartbeat.sh stop
```

## 📁 文件结构

```
/workspaces/RickyGB/
├── gateway_heartbeat.py      # 主检测脚本
├── manage_heartbeat.sh       # 服务管理脚本
├── test_heartbeat.sh         # 测试脚本
├── setup_heartbeat.sh        # 安装脚本
├── heartbeat_config.json     # 配置文件
└── README_HEARTBEAT.md       # 本文档
```

## ⚙️ 配置说明

### 配置文件 `heartbeat_config.json`
```json
{
    "monitor": {
        "interval_minutes": 5,           # 检查间隔（分钟）
        "channel": "slack",              # 消息通道
        "target_channel": "#initclawdbot", # 目标频道
        "test_message": "网关心跳检测"    # 测试消息
    },
    "retry_settings": {
        "first_retry_wait": 30,          # 第一次重试等待（秒）
        "second_retry_wait": 40,         # 第二次重试等待（秒）
        "third_retry_wait": 50           # 第三次重试等待（秒）
    }
}
```

### 命令行参数
```bash
# 基本用法
python3 gateway_heartbeat.py

# 自定义配置
python3 gateway_heartbeat.py \
  --interval 5 \           # 检查间隔（分钟）
  --channel slack \        # 消息通道
  --target "#channel" \    # 目标频道
  --message "测试消息"     # 测试消息内容

# 单次检查模式
python3 gateway_heartbeat.py --once
```

## 🛠️ 系统集成

### Systemd服务
安装脚本会自动创建systemd服务：
```bash
# 服务文件位置
/etc/systemd/system/clawdbot-heartbeat.service

# 管理命令
sudo systemctl start clawdbot-heartbeat
sudo systemctl status clawdbot-heartbeat
sudo systemctl stop clawdbot-heartbeat
```

### Cron任务（备选方案）
如果systemd不可用，会自动创建cron任务：
```
*/5 * * * * /usr/bin/python3 /path/to/gateway_heartbeat.py --once
```

## 📊 日志系统

### 日志文件位置
```
~/.clawdbot/logs/
├── gateway_heartbeat.log          # 主日志文件
├── heartbeat-service.log          # systemd服务输出
├── heartbeat-service-error.log    # systemd错误输出
└── heartbeat-cron.log             # cron任务输出
```

### 日志格式
```
2026-01-31 12:00:00 - INFO - 开始执行心跳检查
2026-01-31 12:00:00 - INFO - 发送测试消息: 网关心跳检测 - 2026-01-31 12:00:00
2026-01-31 12:00:30 - WARNING - 第一次重试: 未检测到网关响应
2026-01-31 12:01:10 - ERROR - 所有心跳检查失败，准备重启网关
2026-01-31 12:01:15 - INFO - 网关重启成功
```

## 🔧 故障排除

### 常见问题

#### 1. 权限问题
```bash
# 如果遇到权限错误
sudo chmod +x gateway_heartbeat.py
sudo chmod +x manage_heartbeat.sh
```

#### 2. 服务无法启动
```bash
# 检查服务状态
sudo systemctl status clawdbot-heartbeat

# 查看详细日志
journalctl -u clawdbot-heartbeat -f
```

#### 3. 消息发送失败
```bash
# 测试clawdbot命令
clawdbot message send --channel slack --target "#initclawdbot" --message "测试"

# 检查网络连接
ping 8.8.8.8
```

#### 4. 网关重启失败
```bash
# 手动检查网关状态
clawdbot gateway status

# 手动重启网关
clawdbot gateway restart
```

### 调试模式
```bash
# 启用详细日志
python3 gateway_heartbeat.py --once --channel slack 2>&1 | tee debug.log

# 检查环境变量
echo $PATH
which python3
which clawdbot
```

## 🎯 使用场景

### GitHub Codespace环境
```bash
# 在Codespace启动时自动运行
echo "./manage_heartbeat.sh start" >> ~/.bashrc

# 或者添加到.devcontainer配置
```

### 生产环境部署
```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 配置服务
sudo ./setup_heartbeat.sh

# 3. 启用监控
sudo systemctl enable --now clawdbot-heartbeat

# 4. 设置日志轮转
sudo cp heartbeat-logrotate /etc/logrotate.d/
```

### 开发环境测试
```bash
# 模拟网关故障测试
./test_heartbeat.sh

# 压力测试
for i in {1..10}; do
    python3 gateway_heartbeat.py --once
    sleep 10
done
```

## 📈 监控和告警

### 健康检查端点
```bash
# 添加健康检查（可选）
curl http://localhost:8080/health 2>/dev/null || echo "服务异常"
```

### 集成到现有监控
```bash
# Nagios/Icinga检查
check_heartbeat() {
    if tail -n 10 ~/.clawdbot/logs/gateway_heartbeat.log | grep -q "心跳检查通过"; then
        echo "OK - 心跳检测正常"
        exit 0
    else
        echo "CRITICAL - 心跳检测异常"
        exit 2
    fi
}
```

## 🔄 更新和维护

### 更新脚本
```bash
# 拉取最新代码
git pull origin main

# 重新安装
./setup_heartbeat.sh

# 重启服务
sudo ./manage_heartbeat.sh restart
```

### 备份配置
```bash
# 备份配置文件
cp heartbeat_config.json heartbeat_config.json.backup

# 备份日志
tar -czf heartbeat-logs-$(date +%Y%m%d).tar.gz ~/.clawdbot/logs/
```

## 📝 版本历史

### v1.0.0 (2026-01-31)
- 初始版本发布
- 实现基本心跳检测功能
- 添加三级重试机制
- 支持自动重启网关
- 完整的日志系统
- systemd和cron集成

## 📄 许可证

MIT License

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 🆘 获取帮助

如果遇到问题：
1. 查看日志文件：`~/.clawdbot/logs/gateway_heartbeat.log`
2. 运行测试脚本：`./test_heartbeat.sh`
3. 检查服务状态：`./manage_heartbeat.sh status`
4. 提交Issue到GitHub仓库