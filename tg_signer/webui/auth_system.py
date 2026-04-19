"""
WebUI认证和用户管理系统
提供前端化的账号登录和状态管理
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Any

from nicegui import app, ui


class WebAuthSystem:
    """WebUI前端化认证系统"""

    def __init__(self):
        self.current_user = None
        self.session_data = {}
        self.auth_state = "login"  # login, dashboard, error
        self.login_attempts = 0
        self.max_attempts = 5
        self.lockout_time = 300  # 5分钟锁定
        self.last_attempt = 0

    def check_rate_limit(self) -> bool:
        """检查速率限制"""
        current_time = time.time()
        if self.login_attempts >= self.max_attempts:
            if current_time - self.last_attempt < self.lockout_time:
                return False
            else:
                # 重置尝试次数
                self.login_attempts = 0
        return True

    def record_attempt(self, success: bool):
        """记录登录尝试"""
        self.last_attempt = time.time()
        if success:
            self.login_attempts = 0
        else:
            self.login_attempts += 1

    async def web_login(self, username: str, password: str, phone_code: str = None) -> dict:
        """
        前端化登录流程
        返回: {'success': bool, 'data': dict, 'error': str}
        """
        try:
            if not self.check_rate_limit():
                return {
                    'success': False,
                    'error': f'登录失败次数过多，请等待{self.lockout_time//60}分钟后重试'
                }

            # 模拟Telegram登录流程
            login_result = await self._simulate_telegram_login(username, password, phone_code)

            if login_result['success']:
                # 保存会话数据
                self.current_user = login_result['user_data']
                self.session_data = login_result['session_data']

                # 记录成功尝试
                self.record_attempt(True)

                return {
                    'success': True,
                    'data': {
                        'user_id': login_result['user_data']['id'],
                        'username': login_result['user_data'].get('username'),
                        'first_name': login_result['user_data'].get('first_name'),
                        'phone_number': login_result['user_data'].get('phone_number'),
                        'session_file': login_result['session_data']['session_path']
                    }
                }
            else:
                self.record_attempt(False)
                return login_result

        except Exception as e:
            self.record_attempt(False)
            return {
                'success': False,
                'error': f'登录过程中发生错误: {str(e)}'
            }

    async def _simulate_telegram_login(self, username: str, password: str, phone_code: str) -> dict:
        """
        模拟Telegram登录（实际项目中需要集成Telegram API）
        """
        # 这里应该调用实际的Telegram登录API
        # 为了演示，我们创建一个模拟的登录流程

        # 验证基本输入
        if not username or len(username) < 3:
            return {'success': False, 'error': '用户名至少需要3个字符'}

        if not password or len(password) < 6:
            return {'success': False, 'error': '密码至少需要6个字符'}

        if phone_code and len(phone_code) != 5:
            return {'success': False, 'error': '验证码格式不正确'}

        # 模拟网络延迟
        await asyncio.sleep(2)

        # 模拟成功登录（实际项目需要真实验证）
        user_data = {
            'id': 123456789,
            'username': username,
            'first_name': 'Test',
            'last_name': 'User',
            'phone_number': '+8613800138000',
            'is_bot': False,
            'is_premium': False
        }

        session_data = {
            'session_path': f'/tmp/session_{username}.session',
            'api_id': os.environ.get('TG_API_ID', 12345),
            'api_hash': os.environ.get('TG_API_HASH', 'your_api_hash'),
            'created_at': time.time(),
            'last_used': time.time()
        }

        return {
            'success': True,
            'user_data': user_data,
            'session_data': session_data,
            'dialogs': self._generate_mock_dialogs()
        }

    def _generate_mock_dialogs(self) -> list:
        """生成模拟对话列表（用于测试）"""
        return [
            {
                'id': -100123456789,
                'title': '测试群组',
                'type': 'supergroup',
                'username': 'test_group',
                'unread_count': 5,
                'last_message_date': time.time() - 3600
            },
            {
                'id': -100234567890,
                'title': '签到频道',
                'type': 'channel',
                'username': 'checkin_channel',
                'unread_count': 0,
                'last_message_date': time.time() - 7200
            },
            {
                'id': 987654321,
                'title': '个人聊天',
                'type': 'private',
                'username': 'friend_user',
                'unread_count': 1,
                'last_message_date': time.time() - 1800
            }
        ]

    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        return self.current_user

    def get_session_info(self) -> Optional[Dict]:
        """获取会话信息"""
        return self.session_data

    def logout(self):
        """登出"""
        self.current_user = None
        self.session_data = {}
        self.auth_state = "login"
        # 清除app存储中的用户数据
        app.storage.user.clear()

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.current_user is not None


# 全局认证系统实例
auth_system = WebAuthSystem()


def create_login_ui(container) -> None:
    """创建前端化登录界面"""
    with container:
        ui.label("TG Signer Web 控制台").classes(
            "text-2xl font-semibold tracking-wide mb-2"
        )
        ui.label("欢迎使用增强版TG Signer！").classes(
            "text-gray-600 mb-6"
        )

        with ui.card().classes("w-full max-w-md shadow-lg"):
            ui.label("账号登录").classes("text-xl font-bold text-center mb-4")

            with ui.column().classes("w-full gap-4"):
                # 用户名输入
                username_input = ui.input(
                    label="Telegram用户名",
                    placeholder="@username 或手机号",
                    on_change=lambda e: update_username_status(e.value)
                ).classes("w-full").props("outlined")

                # 密码输入
                password_input = ui.input(
                    label="密码",
                    placeholder="请输入密码",
                    password=True,
                    password_toggle_button=True,
                    on_change=lambda e: update_password_status(e.value)
                ).classes("w-full").props("outlined")

                # 验证码输入 (可选)
                phone_code_input = ui.input(
                    label="验证码 (可选)",
                    placeholder="短信验证码",
                    on_change=lambda e: update_phone_status(e.value)
                ).classes("w-full").props("outlined")
                phone_code_input.disable()

                # 状态显示
                status_label = ui.label("").classes("text-sm text-negative w-full text-center")

                # 登录按钮
                login_button = ui.button(
                    "🚀 开始登录",
                    color="primary",
                    on_click=lambda: handle_login(username_input, password_input, phone_code_input, status_label)
                ).classes("w-full mt-2")

                # 切换验证码输入
                toggle_code_btn = ui.button(
                    "📱 获取验证码",
                    color="secondary",
                    on_click=lambda: toggle_phone_code()
                ).classes("w-full").props("outline")

            # 底部说明
            ui.label("💡 提示: 首次登录会自动创建会话文件").classes(
                "text-xs text-gray-500 text-center mt-4"
            )


def update_username_status(value: str):
    """更新用户名状态"""
    if value and len(value) >= 3:
        username_input.classes("border-green-500")
    else:
        username_input.classes("border-red-500")


def update_password_status(value: str):
    """更新密码状态"""
    if value and len(value) >= 6:
        password_input.classes("border-green-500")
    else:
        password_input.classes("border-red-500")


def update_phone_status(value: str):
    """更新验证码状态"""
    if value and len(value) == 5:
        phone_code_input.classes("border-green-500")
    else:
        phone_code_input.classes("border-blue-500")


async def handle_login(username_input, password_input, phone_code_input, status_label):
    """处理登录逻辑"""
    username = username_input.value.strip()
    password = password_input.value
    phone_code = phone_code_input.value if phone_code_input.value else None

    # 验证输入
    if not username or len(username) < 3:
        status_label.text = "用户名至少需要3个字符"
        status_label.update()
        return

    if not password or len(password) < 6:
        status_label.text = "密码至少需要6个字符"
        status_label.update()
        return

    # 禁用按钮防止重复点击
    login_button.disable()
    login_button.text = "⏳ 登录中..."

    try:
        # 执行登录
        result = await auth_system.web_login(username, password, phone_code)

        if result['success']:
            status_label.text = "🎉 登录成功！正在跳转..."
            status_label.classes("text-green-600")
            status_label.update()

            # 保存登录状态到app storage
            app.storage.user.update({
                'username': username,
                'login_time': time.time(),
                'user_data': result['data']
            })

            # 延迟跳转到主界面
            await asyncio.sleep(1)
            render_dashboard()

        else:
            status_label.text = f"❌ 登录失败: {result['error']}"
            status_label.classes("text-red-600")
            status_label.update()

    except Exception as e:
        status_label.text = f"❌ 系统错误: {str(e)}"
        status_label.classes("text-red-600")
        status_label.update()

    finally:
        # 重新启用按钮
        login_button.enable()
        login_button.text = "🚀 开始登录"


def toggle_phone_code():
    """切换验证码输入"""
    if phone_code_input.disabled:
        phone_code_input.enable()
        toggle_code_btn.text = "🔒 隐藏验证码"
    else:
        phone_code_input.disable()
        toggle_code_btn.text = "📱 获取验证码"


def check_login_status() -> bool:
    """检查登录状态"""
    return auth_system.is_logged_in() or bool(app.storage.user.get('username'))


def render_dashboard():
    """渲染主仪表板"""
    root.clear()
    _build_enhanced_dashboard(root)


def _build_enhanced_dashboard(container):
    """构建增强版仪表板"""
    with container:
        # 顶部用户信息显示
        if auth_system.get_current_user():
            with ui.row().classes("w-full items-center justify-between mb-4"):
                user_info = auth_system.get_current_user()
                ui.label(f"👋 欢迎, {user_info.get('first_name', '用户')}!")
                ui.button("🔓 退出登录", on_click=handle_logout).props("flat")

        # 原有的仪表板内容
        ui.label("TG Signer Web 控制台").classes(
            "text-2xl font-semibold tracking-wide mb-2"
        )
        refreshers = []
        refresh_records = None

        def refresh_all():
            for refresh in refreshers:
                refresh()

        # 基础设置区域
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("items-center justify-between"):
                ui.label("基础设置").classes("text-lg font-semibold")
                ui.label(f"工作目录: {state.workdir}").classes("text-sm text-gray-500")

        # 标签页
        with ui.tabs().classes("w-full") as tabs:
            tab_configs = ui.tab("配置管理")
            tab_users = ui.tab("用户信息")
            tab_records = ui.tab("签到记录")
            tab_logs = ui.tab("日志")

        def goto_records(task_name: str):
            tabs.value = tab_records
            tabs.update()
            if refresh_records:
                refresh_records.filter_input.set_value(task_name)

        with ui.tab_panels(tabs, value=tab_configs).classes("w-full"):
            with ui.tab_panel(tab_configs):
                ui.label("管理 signer 和 monitor 的配置文件").classes("text-gray-600")
                with ui.tabs().classes("mt-2") as sub_tabs:
                    tab_signer = ui.tab("Signer")
                    tab_monitor = ui.tab("Monitor")
                with ui.tab_panels(sub_tabs, value=tab_signer).classes("w-full"):
                    with ui.tab_panel(tab_signer):
                        refreshers.append(SignerBlock(SIGNER_TEMPLATE, goto_records=goto_records))
                    with ui.tab_panel(tab_monitor):
                        refreshers.append(MonitorBlock(MONITOR_TEMPLATE))

            with ui.tab_panel(tab_users):
                # 显示用户信息和最近对话
                if auth_system.get_current_user():
                    display_user_info()
                else:
                    ui.label("请先登录").classes("text-gray-500")

            with ui.tab_panel(tab_records):
                refresh_records = SignRecordBlock()
                refreshers.append(refresh_records)

            with ui.tab_panel(tab_logs):
                refreshers.append(log_block())

        refresh_all()


def display_user_info():
    """显示用户信息"""
    user_data = auth_system.get_current_user()
    session_data = auth_system.get_session_info()

    with ui.column().classes("w-full gap-4"):
        # 用户基本信息
        with ui.card().classes("w-full"):
            ui.label("用户信息").classes("font-bold")
            with ui.grid(columns=2).classes("w-full"):
                ui.label("用户ID:").classes("font-medium")
                ui.label(str(user_data.get('id')))
                ui.label("用户名:").classes("font-medium")
                ui.label(user_data.get('username', 'N/A'))
                ui.label("姓名:").classes("font-medium")
                ui.label(f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip())
                ui.label("手机号:").classes("font-medium")
                ui.label(user_data.get('phone_number', 'N/A'))

        # 会话信息
        if session_data:
            with ui.card().classes("w-full"):
                ui.label("会话信息").classes("font-bold")
                with ui.grid(columns=2).classes("w-full"):
                    ui.label("会话文件:").classes("font-medium")
                    ui.label(os.path.basename(session_data.get('session_path')))
                    ui.label("创建时间:").classes("font-medium")
                    ui.label(time.ctime(session_data.get('created_at')))
                    ui.label("最后使用:").classes("font-medium")
                    ui.label(time.ctime(session_data.get('last_used')))

        # 最近对话
        dialogs = session_data.get('dialogs', []) if session_data else []
        if dialogs:
            with ui.card().classes("w-full"):
                ui.label(f"最近对话 ({len(dialogs)})").classes("font-bold")
                for dialog in dialogs[:5]:  # 显示前5个
                    with ui.row().classes("w-full justify-between items-center p-2 bg-gray-50 rounded"):
                        title = dialog.get('title', '未知')
                        dialog_type = dialog.get('type', 'unknown')
                        unread = dialog.get('unread_count', 0)
                        username = dialog.get('username', '')
                        
                        type_icon = {
                            'private': '👤',
                            'group': '👥', 
                            'supergroup': '🏢',
                            'channel': '📢'
                        }.get(dialog_type, '❓')

                        with ui.column().classes("flex-grow"):
                            ui.label(f"{type_icon} {title}").classes("font-medium")
                            if username:
                                ui.label(f"@{username}").classes("text-sm text-gray-600")
                        
                        if unread > 0:
                            ui.badge(unread, color="red").classes("ml-auto")


def handle_logout():
    """处理登出"""
    auth_system.logout()
    app.storage.user.clear()
    container.clear()
    create_login_ui(container)


# 必要的导入（在实际文件中需要添加到顶部）
import asyncio
import os
import time
from datetime import datetime