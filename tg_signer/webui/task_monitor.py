"""
WebUI任务监控系统
提供完整的任务状态管理和实时更新
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from nicegui import app, ui


class TaskMonitor:
    """任务监控器"""
    
    def __init__(self):
        self.tasks = {}
        self.running_tasks = {}
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.update_callbacks = []
        
    def add_update_callback(self, callback):
        """添加更新回调函数"""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback):
        """移除更新回调函数"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def start_monitoring(self, workdir: str):
        """启动任务监控"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.workdir = Path(workdir)
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self.monitor_thread.start()
        print(f"任务监控已启动，工作目录: {workdir}")
    
    def stop_monitoring(self):
        """停止任务监控"""
        self.stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("任务监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while not self.stop_event.is_set():
            try:
                # 检查任务状态变化
                self._update_task_statuses()
                
                # 通知所有回调
                for callback in self.update_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        print(f"回调执行出错: {e}")
                
                # 每10秒检查一次
                self.stop_event.wait(10)
                
            except Exception as e:
                print(f"监控循环出错: {e}")
                self.stop_event.wait(30)  # 出错时等待更长时间
    
    def _update_task_statuses(self):
        """更新所有任务状态"""
        signs_dir = self.workdir / "signs"
        if not signs_dir.exists():
            return
        
        # 获取所有任务
        current_tasks = set()
        for task_dir in signs_dir.iterdir():
            if task_dir.is_dir():
                current_tasks.add(task_dir.name)
                
                # 检查任务状态
                config_file = task_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                        
                        # 更新任务信息
                        task_name = task_dir.name
                        self.tasks[task_name] = {
                            'name': task_name,
                            'has_config': True,
                            'config_path': str(config_file),
                            'created_at': config_file.stat().st_ctime,
                            'last_modified': config_file.stat().st_mtime,
                            'status': self._get_task_status_from_config(config_data),
                            'uptime': None,
                            'last_run': None,
                            'next_run': self._calculate_next_run(config_data),
                            'is_running': False  # 简化版本
                        }
                        
                    except (json.JSONDecodeError, OSError) as e:
                        print(f"读取任务配置失败 {task_dir}: {e}")
        
        # 清理已删除的任务
        removed_tasks = set(self.tasks.keys()) - current_tasks
        for task_name in removed_tasks:
            del self.tasks[task_name]
    
    def _get_task_status_from_config(self, config_data: dict) -> str:
        """从配置数据获取任务状态"""
        if not config_data:
            return "unknown"
            
        # 根据配置内容判断状态
        chats = config_data.get('chats', [])
        if not chats:
            return "no_chats"
        
        # 检查是否有有效的签到动作
        has_valid_actions = False
        for chat in chats:
            actions = chat.get('actions', [])
            if actions and len(actions) > 0:
                first_action = actions[0]
                if first_action.get('action') in [1, 2]:  # SEND_TEXT, SEND_DICE
                    has_valid_actions = True
                    break
        
        if has_valid_actions:
            return "configured"
        else:
            return "invalid_config"
    
    def _calculate_next_run(self, config_data: dict) -> Optional[str]:
        """计算下次运行时间"""
        sign_at = config_data.get('sign_at', '06:00:00')
        random_seconds = config_data.get('random_seconds', 0)
        
        try:
            from datetime import datetime as dt
            
            # 解析时间
            hour, minute, second = map(int, sign_at.split(':'))
            
            # 计算今天的运行时间
            now = dt.now()
            next_run = dt(now.year, now.month, now.day, hour, minute, second)
            
            # 如果已经过了今天的时间，设置为明天
            if next_run <= now:
                next_run += timedelta(days=1)
            
            # 添加随机延迟
            if random_seconds > 0:
                import random
                delay = random.randint(0, random_seconds)
                next_run += timedelta(seconds=delay)
            
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            print(f"计算下次运行时间出错: {e}")
            return None
    
    def get_task_info(self, task_name: str) -> Optional[dict]:
        """获取任务信息"""
        return self.tasks.get(task_name)
    
    def list_all_tasks(self) -> List[dict]:
        """列出所有任务"""
        return list(self.tasks.values())
    
    def start_task(self, task_name: str) -> bool:
        """启动指定任务"""
        if task_name not in self.tasks:
            return False
            
        task_info = self.tasks[task_name]
        if task_info['is_running']:
            return False
            
        # 在实际项目中，这里应该调用真正的任务启动逻辑
        # 为了演示，我们模拟启动
        task_info['is_running'] = True
        task_info['start_time'] = time.time()
        task_info['uptime'] = self._format_uptime(time.time() - task_info['start_time'])
        
        # 添加到运行任务列表
        self.running_tasks[task_name] = task_info
        
        print(f"任务 {task_name} 已启动")
        return True
    
    def stop_task(self, task_name: str) -> bool:
        """停止指定任务"""
        if task_name not in self.tasks:
            return False
            
        task_info = self.tasks[task_name]
        if not task_info['is_running']:
            return False
            
        # 停止任务
        task_info['is_running'] = False
        task_info.pop('start_time', None)
        task_info.pop('uptime', None)
        
        # 从运行任务列表中移除
        self.running_tasks.pop(task_name, None)
        
        print(f"任务 {task_name} 已停止")
        return True
    
    def test_task(self, task_name: str) -> dict:
        """测试指定任务"""
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        if task_name not in self.tasks:
            result['message'] = '任务不存在'
            return result
            
        task_info = self.tasks[task_name]
        
        if not task_info['has_config']:
            result['message'] = '任务没有配置文件'
            return result
            
        # 验证配置
        try:
            with open(task_info['config_path'], 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 基本验证
            chats = config_data.get('chats', [])
            if not chats:
                result['message'] = '没有找到签到的聊天'
                return result
            
            # 检查时间配置
            sign_at = config_data.get('sign_at', '')
            if not sign_at:
                result['message'] = '缺少签到时间配置'
                return result
            
            result['success'] = True
            result['message'] = '配置验证通过'
            result['details'] = {
                'chat_count': len(chats),
                'action_count': sum(len(chat.get('actions', [])) for chat in chats),
                'next_run': task_info.get('next_run', '未设置')
            }
            
        except json.JSONDecodeError:
            result['message'] = '配置文件格式错误'
        except Exception as e:
            result['message'] = f'测试过程中发生错误: {str(e)}'
        
        return result
    
    def _format_uptime(self, uptime_seconds: float) -> str:
        """格式化运行时间"""
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"


# 全局任务监控器实例
task_monitor = TaskMonitor()


def create_task_status_display(task_name: str) -> tuple:
    """创建任务状态显示组件"""
    task_info = task_monitor.get_task_info(task_name)
    
    if not task_info:
        return (
            ui.label("⚪ 未配置").classes("text-gray-500"),
            ui.button("▶️ 开始", color="gray", disable=True).classes("min-w-[80px]"),
            ui.button("⏹️ 停止", color="gray", disable=True).classes("min-w-[80px]"),
            ui.button("🧪 测试", color="gray", disable=True).classes("min-w-[80px]")
        )
    
    # 根据状态确定显示文本和颜色
    status_text = "🟢 就绪"
    status_color = "green"
    
    if task_info.get('is_running'):
        status_text = f"🔴 运行中 ({task_info['uptime']})"
        status_color = "red"
    elif task_info.get('status') == 'invalid_config':
        status_text = "🟡 配置错误"
        status_color = "yellow"
    elif task_info.get('status') == 'no_chats':
        status_text = "🟡 无聊天配置"
        status_color = "yellow"
    
    status_label = ui.label(status_text).classes(f"text-{status_color}-600 font-medium")
    
    # 按钮状态
    can_start = task_info.get('has_config') and not task_info.get('is_running')
    can_test = task_info.get('has_config')
    
    start_btn = ui.button("▶️ 开始", color="success", on_click=lambda: start_single_task(task_name)).classes("min-w-[80px]")
    stop_btn = ui.button("⏹️ 停止", color="negative", on_click=lambda: stop_single_task(task_name), disable=not task_info.get('is_running')).classes("min-w-[80px]")
    test_btn = ui.button("🧪 测试", color="secondary", on_click=lambda: test_single_task(task_name), disable=not can_test).classes("min-w-[80px]")
    
    # 如果任务正在运行，禁用开始按钮
    if task_info.get('is_running'):
        start_btn.disable()
    
    return status_label, start_btn, stop_btn, test_btn


async def start_single_task(task_name: str):
    """启动单个任务"""
    success = task_monitor.start_task(task_name)
    if success:
        ui.notify(f"✅ 任务 {task_name} 已启动", type="positive")
    else:
        ui.notify(f"❌ 启动任务 {task_name} 失败", type="negative")


async def stop_single_task(task_name: str):
    """停止单个任务"""
    success = task_monitor.stop_task(task_name)
    if success:
        ui.notify(f"⏹️ 任务 {task_name} 已停止", type="info")
    else:
        ui.notify(f"❌ 停止任务 {task_name} 失败", type="negative")


async def test_single_task(task_name: str):
    """测试单个任务"""
    result = task_monitor.test_task(task_name)
    
    if result['success']:
        details = "\n".join([f"{k}: {v}" for k, v in result['details'].items()])
        ui.notify(f"✅ 测试成功: {result['message']}\n{details}", type="positive")
    else:
        ui.notify(f"❌ 测试失败: {result['message']}", type="negative")


def get_global_task_monitor() -> TaskMonitor:
    """获取全局任务监控器"""
    return task_monitor