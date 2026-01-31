#!/usr/bin/env python3
"""
Clawdbot网关心跳检测脚本
用于检测Clawdbot网关是否活跃，如果无响应则自动重启
"""

import os
import sys
import time
import logging
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# 配置日志
def setup_logger():
    """设置日志配置"""
    log_dir = Path.home() / ".clawdbot" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "gateway_heartbeat.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

class GatewayHeartbeatMonitor:
    """Clawdbot网关心跳监控器"""
    
    def __init__(self, channel="slack", target_channel=None, test_message="网关心跳检测"):
        """
        初始化监控器
        
        Args:
            channel: 消息发送通道 (slack, telegram, etc.)
            target_channel: 目标频道/聊天ID
            test_message: 测试消息内容
        """
        self.channel = channel
        self.target_channel = target_channel
        self.test_message = test_message
        self.last_response_time = None
        self.message_id = None
        
        # 重试配置
        self.retry_config = [
            {"wait": 30, "name": "第一次重试"},
            {"wait": 40, "name": "第二次重试"},
            {"wait": 50, "name": "第三次重试"}
        ]
        
        logger.info(f"初始化网关心跳监控器，通道: {channel}")
    
    def send_test_message(self):
        """发送测试消息到AI"""
        try:
            # 构建clawdbot命令
            cmd = ["clawdbot", "message", "send"]
            
            # 添加通道参数
            if self.channel:
                cmd.extend(["--channel", self.channel])
            
            # 添加目标频道参数
            if self.target_channel:
                cmd.extend(["--target", self.target_channel])
            else:
                # 如果没有指定目标，发送到默认位置
                cmd.extend(["--target", "#initclawdbot"])
            
            # 添加消息内容
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"{self.test_message} - {timestamp}"
            cmd.extend(["--message", message])
            
            logger.info(f"发送测试消息: {message}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("测试消息发送成功")
                # 尝试从输出中提取消息ID
                if "messageId" in result.stdout:
                    import json
                    try:
                        output_lines = result.stdout.strip().split('\n')
                        for line in output_lines:
                            if line.startswith('{'):
                                data = json.loads(line)
                                if 'result' in data and 'messageId' in data['result']:
                                    self.message_id = data['result']['messageId']
                                    logger.info(f"获取到消息ID: {self.message_id}")
                                    break
                    except:
                        pass
                return True
            else:
                logger.error(f"发送测试消息失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("发送测试消息超时")
            return False
        except Exception as e:
            logger.error(f"发送测试消息时发生错误: {e}")
            return False
    
    def check_gateway_status(self):
        """检查网关状态 - 改进版本"""
        try:
            # 使用clawdbot gateway status命令检查状态
            cmd = ["clawdbot", "gateway", "status"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # 多种方式检测网关状态
                status_indicators = [
                    ("RPC probe: ok", "RPC探测成功"),
                    ("Listening:", "正在监听"),
                    ("Runtime:", "运行时间"),
                    ("running", "运行中"),
                    ("active", "活跃"),
                    ("ok", "正常")
                ]
                
                # 检查是否有任何状态指示器
                for indicator, description in status_indicators:
                    if indicator.lower() in output.lower():
                        logger.info(f"网关状态: {description}")
                        return True
                
                # 如果没有找到明确的运行状态，但命令成功执行，也认为是正常的
                # 检查是否有明显的错误信息
                error_indicators = [
                    "failed",
                    "error",
                    "not running",
                    "stopped",
                    "dead"
                ]
                
                for error in error_indicators:
                    if error in output.lower():
                        logger.warning(f"网关状态异常: 检测到 '{error}'")
                        return False
                
                # 默认情况：命令成功但没有明确状态，认为是正常的
                logger.info("网关状态: 命令执行成功（状态不明确）")
                return True
                
            else:
                logger.error(f"检查网关状态失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("检查网关状态超时")
            return False
        except Exception as e:
            logger.error(f"检查网关状态时发生错误: {e}")
            return False
    
    def wait_for_response(self, wait_time):
        """等待响应"""
        logger.info(f"等待 {wait_time} 秒检查响应...")
        time.sleep(wait_time)
        
        # 这里可以添加更复杂的响应检查逻辑
        # 例如：检查是否有新消息、检查特定消息ID的响应等
        # 目前简化：只要网关状态正常就认为有响应
        
        return self.check_gateway_status()
    
    def restart_gateway(self):
        """重启网关"""
        try:
            logger.warning("尝试重启网关...")
            
            # 先停止网关
            stop_cmd = ["clawdbot", "gateway", "stop"]
            stop_result = subprocess.run(
                stop_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if stop_result.returncode == 0:
                logger.info("网关停止成功")
            else:
                logger.warning(f"停止网关时遇到问题: {stop_result.stderr}")
            
            # 等待2秒
            time.sleep(2)
            
            # 启动网关
            start_cmd = ["clawdbot", "gateway", "start"]
            start_result = subprocess.run(
                start_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if start_result.returncode == 0:
                logger.info("网关启动成功")
                return True
            else:
                logger.error(f"启动网关失败: {start_result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"重启网关时发生错误: {e}")
            return False
    
    def run_heartbeat_check(self):
        """执行一次完整的心跳检查"""
        logger.info("开始执行心跳检查")
        
        # 步骤1: 发送测试消息
        if not self.send_test_message():
            logger.warning("首次发送测试消息失败，直接进入重试流程")
        
        # 步骤2-4: 三级重试机制
        for i, retry in enumerate(self.retry_config):
            wait_time = retry["wait"]
            retry_name = retry["name"]
            
            logger.info(f"{retry_name} (等待{wait_time}秒)")
            
            # 等待并检查响应
            if self.wait_for_response(wait_time):
                logger.info(f"{retry_name}: 检测到网关响应，检查通过")
                self.last_response_time = datetime.now()
                return True
            
            logger.warning(f"{retry_name}: 未检测到网关响应")
            
            # 如果是最后一次重试，发送最后一次测试消息
            if i == len(self.retry_config) - 1:
                logger.warning("所有重试尝试均失败，发送最终测试消息")
                self.send_test_message()
                time.sleep(5)  # 等待5秒
        
        # 所有重试都失败，重启网关
        logger.error("所有心跳检查失败，准备重启网关")
        if self.restart_gateway():
            logger.info("网关重启成功")
            # 等待网关启动
            time.sleep(10)
            # 验证网关状态
            if self.check_gateway_status():
                logger.info("网关重启后状态正常")
                return True
            else:
                logger.error("网关重启后状态异常")
                return False
        else:
            logger.error("网关重启失败")
            return False
    
    def run_continuous_monitoring(self, interval_minutes=5):
        """持续监控网关"""
        logger.info(f"开始持续监控，检查间隔: {interval_minutes}分钟")
        
        try:
            while True:
                # 记录检查开始时间
                check_start = datetime.now()
                logger.info(f"开始定时检查 - {check_start.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 执行心跳检查
                success = self.run_heartbeat_check()
                
                if success:
                    logger.info(f"心跳检查通过 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.error(f"心跳检查失败 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 计算下一次检查时间
                check_end = datetime.now()
                check_duration = (check_end - check_start).total_seconds()
                wait_seconds = max(0, interval_minutes * 60 - check_duration)
                
                logger.info(f"本次检查耗时: {check_duration:.1f}秒，等待 {wait_seconds:.1f}秒后继续")
                
                # 等待下一次检查
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                    
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止监控")
        except Exception as e:
            logger.error(f"监控过程中发生错误: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Clawdbot网关心跳检测脚本')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='检查间隔时间（分钟），默认5分钟')
    parser.add_argument('--channel', '-c', type=str, default='slack',
                       help='消息发送通道，默认slack')
    parser.add_argument('--target', '-t', type=str, 
                       help='目标频道/聊天ID，默认使用配置的默认值')
    parser.add_argument('--message', '-m', type=str, default='网关心跳检测',
                       help='测试消息内容，默认"网关心跳检测"')
    parser.add_argument('--once', '-o', action='store_true',
                       help='只执行一次检查，不持续监控')
    
    args = parser.parse_args()
    
    # 创建监控器
    monitor = GatewayHeartbeatMonitor(
        channel=args.channel,
        target_channel=args.target,
        test_message=args.message
    )
    
    logger.info(f"网关心跳检测配置:")
    logger.info(f"  检查间隔: {args.interval}分钟")
    logger.info(f"  消息通道: {args.channel}")
    logger.info(f"  目标频道: {args.target or '默认'}")
    logger.info(f"  测试消息: {args.message}")
    logger.info(f"  运行模式: {'单次检查' if args.once else '持续监控'}")
    
    if args.once:
        # 单次检查模式
        success = monitor.run_heartbeat_check()
        if success:
            logger.info("单次心跳检查: 通过")
            sys.exit(0)
        else:
            logger.error("单次心跳检查: 失败")
            sys.exit(1)
    else:
        # 持续监控模式
        monitor.run_continuous_monitoring(interval_minutes=args.interval)

if __name__ == "__main__":
    main()