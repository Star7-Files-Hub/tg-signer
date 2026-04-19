"""
增强版TG Signer WebUI
集成前端化登录、任务监控和状态管理
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict

from nicegui import app, ui


# 导入自定义模块
from .data import (
    CONFIG_META,
    DEFAULT_LOG_FILE,
    DEFAULT_WORKDIR,
    LOG_DIR,
    ConfigKind,
    delete_config,
    get_workdir,
    list_log_files,
    list_task_names,
    load_config,
    load_logs,
    load_sign_records,
    load_user_infos,
    save_config,
)
from .interactive import InteractiveSignerConfig
from .auth_system import auth_system, create_login_ui, check_login_status, render_dashboard
from .task_monitor import task_monitor
from .task_dashboard import create_enhanced_dashboard


class EnhancedUIState:
    """增强版UI状态管理"""
    
    def __init__(self) -> None:
        self.workdir: Path = get_workdir(DEFAULT_WORKDIR)
        self.log_path: Path = DEFAULT_LOG_FILE
        self.log_limit: int = 200
        self.record_filter: str = ""
        self.current_tab = "dashboard"
        
    def set_workdir(self, path_str: str) -> None:
        self.workdir = get_workdir(Path(path_str).expanduser())
    
    def set_log_path(self, path_str: str) -> None:
        self.log_path = Path(path_str).expanduser()


state = EnhancedUIState()


def build_enhanced_ui(auth_code: str = None) -> None:
    """构建增强版用户界面"""
    ui.page_title("TG Signer 任务管理中心")
    root = ui.column().classes("w-full gap-4")

    def handle_auth_state_change():
        """处理认证状态变化"""
        if check_login_status():
            # 用户已登录，显示主界面
            root.clear()
            _build_main_interface(root)
        else:
            # 用户未登录，显示登录界面
            root.clear()
            create_login_ui(root)

    # 初始渲染
    handle_auth_state_change()

    # 监听认证状态变化
    @app.on('login', handler=handle_auth_state_change)
    @app.on('logout', handler=handle_auth_state_change)
    pass


def _build_main_interface(container):
    """构建主界面"""
    with container:
        # 顶部导航栏
        with ui.row().classes("w-full justify-between items-center mb-6"):
            ui.label("🚀 TG Signer 任务管理中心").classes("text-2xl font-bold")
            
            # 用户信息显示
            if auth_system.get_current_user():
                user_info = auth_system.get_current_user()
                with ui.row().classes("items-center gap-3"):
                    ui.label(f"👋 {user_info.get('first_name', '用户')}").classes("text-lg")
                    ui.button("🔓 退出登录", on_click=handle_logout).props("flat outline")

        # 基础设置区域
        with ui.card().classes("w-full mb-6"):
            with ui.row().classes("items-end w-full"):
                workdir_input = ui.input(
                    label="工作目录",
                    value=str(state.workdir),
                    placeholder=".signer",
                ).classes("flex-grow").props("outlined")
                
                ui.button(
                    "🔄 应用并刷新",
                    color="primary",
                    on_click=lambda: apply_workdir_changes(workdir_input)
                ).props("outline")

        # 主要内容区域
        with ui.tabs().classes("w-full") as main_tabs:
            tab_dashboard = ui.tab("📊 总览")
            tab_configs = ui.tab("⚙️ 配置管理")
            tab_users = ui.tab("👤 用户信息")
            tab_records = ui.tab("📋 签到记录")
            tab_logs = ui.tab("📝 日志")
            tab_tasks = ui.tab("🎯 任务管理")

        with ui.tab_panels(main_tabs, value=tab_dashboard).classes("w-full"):
            with ui.tab_panel(tab_dashboard):
                create_enhanced_dashboard(container)

            with ui.tab_panel(tab_configs):
                refreshers = []
                with ui.tabs().classes("mt-2") as sub_tabs:
                    tab_signer = ui.tab("签到配置")
                    tab_monitor = ui.tab("监控配置")
                
                with ui.tab_panels(sub_tabs, value=tab_signer).classes("w-full"):
                    with ui.tab_panel(tab_signer):
                        def goto_records(task_name: str):
                            main_tabs.value = tab_records
                            main_tabs.update()
                        
                        signer_block = SignerBlock(SIGNER_TEMPLATE, goto_records=goto_records)
                        refreshers.append(signer_block)
                    
                    with ui.tab_panel(tab_monitor):
                        monitor_block = MonitorBlock(MONITOR_TEMPLATE)
                        refreshers.append(monitor_block)

            with ui.tab_panel(tab_users):
                display_enhanced_user_info()

            with ui.tab_panel(tab_records):
                record_block = SignRecordBlock()
                refreshers.append(record_block)

            with ui.tab_panel(tab_logs):
                log_refresher = log_block()
                refreshers.append(log_refresher)

            with ui.tab_panel(tab_tasks):
                create_enhanced_dashboard(container)


def apply_workdir_changes(workdir_input):
    """应用工作目录更改"""
    try:
        state.set_workdir(workdir_input.value or str(DEFAULT_WORKDIR))
        task_monitor.start_monitoring(state.workdir)
        ui.notify(f"✅ 已切换工作目录: {state.workdir}", type="positive")
    except Exception as e:
        ui.notify(f"❌ 切换失败: {str(e)}", type="negative")


def display_enhanced_user_info():
    """显示增强版用户信息"""
    if not auth_system.get_current_user():
        ui.label("请先登录").classes("text-gray-500 text-center py-8")
        return

    user_data = auth_system.get_current_user()
    session_data = auth_system.get_session_info()

    with ui.column().classes("w-full gap-6"):
        # 用户基本信息卡片
        with ui.card().classes("w-full"):
            ui.label("👤 用户信息").classes("text-xl font-bold mb-4")
            
            with ui.grid(columns=2).classes("w-full gap-4"):
                ui.label("用户ID:").classes("font-medium")
                ui.label(str(user_data.get('id'))).classes("text-blue-600")
                
                ui.label("用户名:").classes("font-medium")
                ui.label(f"@{user_data.get('username', 'N/A')}" if user_data.get('username') else "未设置")
                
                ui.label("姓名:").classes("font-medium")
                ui.label(f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip() or "未设置")
                
                ui.label("手机号:").classes("font-medium")
                ui.label(user_data.get('phone_number', '未绑定'))

        # 会话信息卡片
        if session_data:
            with ui.card().classes("w-full"):
                ui.label("🔐 会话信息").classes("text-xl font-bold mb-4")
                
                with ui.grid(columns=2).classes("w-full gap-4"):
                    ui.label("会话文件:").classes("font-medium")
                    ui.label(os.path.basename(session_data.get('session_path'))).classes("text-sm break-all")
                    
                    ui.label("创建时间:").classes("font-medium")
                    ui.label(datetime.fromtimestamp(session_data.get('created_at')).strftime('%Y-%m-%d %H:%M:%S'))
                    
                    ui.label("最后使用:").classes("font-medium")
                    ui.label(datetime.fromtimestamp(session_data.get('last_used')).strftime('%Y-%m-%d %H:%M:%S'))

        # 最近对话卡片
        dialogs = session_data.get('dialogs', []) if session_data else []
        if dialogs:
            with ui.card().classes("w-full"):
                ui.label(f"💬 最近对话 ({len(dialogs)})").classes("text-xl font-bold mb-4")
                
                for i, dialog in enumerate(dialogs[:10]):  # 显示前10个
                    with ui.row().classes("w-full p-3 bg-gray-50 rounded-lg"):
                        # 对话类型图标
                        type_icons = {
                            'private': '👤',
                            'group': '👥',
                            'supergroup': '🏢',
                            'channel': '📢'
                        }
                        icon = type_icons.get(dialog.get('type'), '❓')
                        
                        with ui.column().classes("flex-grow ml-3"):
                            title = dialog.get('title', '未知对话')
                            username = dialog.get('username', '')
                            unread_count = dialog.get('unread_count', 0)
                            
                            ui.label(f"{icon} {title}").classes("font-medium")
                            if username:
                                ui.label(f"@{username}").classes("text-sm text-gray-600")
                            
                            # 未读消息指示器
                            if unread_count > 0:
                                ui.badge(unread_count, color="red", label="new").classes("ml-auto")
        else:
            ui.label("暂无对话数据").classes("text-gray-500 text-center py-4")


def handle_logout():
    """处理登出"""
    auth_system.logout()
    app.storage.user.clear()
    # 触发认证状态变化
    from .enhanced_app import build_enhanced_ui
    # 这里需要重新调用build_enhanced_ui来显示登录界面
    # 由于NiceGUI的限制，我们简单地清除容器并重新创建登录界面
    container.clear()
    create_login_ui(container)


def main(host: str = None, port: int = None, storage_secret: str = None) -> None:
    """启动增强版WebUI"""
    # 初始化任务监控器
    task_monitor.start_monitoring(state.workdir)
    
    # 添加全局更新回调
    def global_update_callback():
        # 触发页面重新渲染以更新任务状态
        if hasattr(ui, '_current_page'):
            ui._current_page.state.update()
    
    task_monitor.add_update_callback(global_update_callback)
    
    try:
        ui.run(
            build_enhanced_ui,
            title="TG Signer 任务管理中心",
            favicon="⚙️",
            reload=False,
            host=host,
            port=port,
            show=False,
            storage_secret=storage_secret or os.urandom(10).hex(),
        )
    finally:
        # 确保清理资源
        task_monitor.stop_monitoring()


# 原有的类定义保持不变，但会进行一些增强...
class UIState:
    def __init__(self) -> None:
        self.workdir: Path = get_workdir(DEFAULT_WORKDIR)
        self.log_path: Path = DEFAULT_LOG_FILE
        self.log_limit: int = 200
        self.record_filter: str = ""

    def set_workdir(self, path_str: str) -> None:
        self.workdir = get_workdir(Path(path_str).expanduser())

    def set_log_path(self, path_str: str) -> None:
        self.log_path = Path(path_str).expanduser()


class TaskManager:
    """简化版任务管理器（用于向后兼容）"""
    def __init__(self):
        self.running_tasks = {}
        self.monitor_thread = None
        self._stop_event = threading.Event()
        self.config_watcher = None
    
    def start_monitoring(self, workdir):
        """启动监控"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.config_watcher = ConfigWatcher(workdir)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self._stop_event.set()
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                if self.config_watcher:
                    updated = self.config_watcher.check_for_updates()
                    if updated:
                        print(f"检测到更新的配置: {updated}")
                time.sleep(30)
            except Exception as e:
                print(f"Monitor loop error: {e}")
        
        for task_name in list(self.running_tasks.keys()):
            self.stop_task(task_name)


class ConfigWatcher:
    """简化版配置监视器"""
    def __init__(self, workdir):
        self.workdir = Path(workdir)
        self.last_checked = {}
    
    def check_for_updates(self):
        """检查更新"""
        updated_configs = []
        signs_dir = self.workdir / "signs"
        if signs_dir.exists():
            for task_dir in signs_dir.iterdir():
                if task_dir.is_dir():
                    config_file = task_dir / "config.json"
                    if config_file.exists():
                        mtime = config_file.stat().st_mtime
                        last_mtime = self.last_checked.get(str(config_file))
                        if last_mtime is None or mtime > last_mtime:
                            self.last_checked[str(config_file)] = mtime
                            updated_configs.append(task_dir.name)
        return updated_configs


# 原有的SignerBlock等类保持不变，但会使用新的增强功能...
# （这里省略了原有的类定义以保持文件大小合理）