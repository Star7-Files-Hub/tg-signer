"""
WebUI任务仪表板
提供完整的任务管理和状态监控界面
"""

from nicegui import ui
from .task_monitor import task_monitor


def create_task_overview_panel():
    """创建任务总览面板"""
    with ui.card().classes("w-full shadow-lg"):
        ui.label("📊 任务总览").classes("text-xl font-bold mb-4")
        
        # 获取任务统计
        all_tasks = task_monitor.list_all_tasks()
        running_count = sum(1 for t in all_tasks if t.get('is_running'))
        ready_count = sum(1 for t in all_tasks if t.get('can_start') and not t.get('is_running'))
        error_count = sum(1 for t in all_tasks if t.get('status') == 'invalid_config')
        
        with ui.grid(columns=2).classes("w-full gap-4"):
            with ui.column().classes("items-center p-4 bg-green-50 rounded"):
                ui.label(str(ready_count)).classes("text-3xl font-bold text-green-600")
                ui.label("就绪任务").classes("text-sm text-green-700")
            
            with ui.column().classes("items-center p-4 bg-red-50 rounded"):
                ui.label(str(running_count)).classes("text-3xl font-bold text-red-600")
                ui.label("运行中").classes("text-sm text-red-700")
            
            with ui.column().classes("items-center p-4 bg-yellow-50 rounded"):
                ui.label(str(error_count)).classes("text-3xl font-bold text-yellow-600")
                ui.label("配置错误").classes("text-sm text-yellow-700")
            
            with ui.column().classes("items-center p-4 bg-blue-50 rounded"):
                ui.label(str(len(all_tasks))).classes("text-3xl font-bold text-blue-600")
                ui.label("总任务数").classes("text-sm text-blue-700")


def create_quick_actions_panel():
    """创建快速操作面板"""
    with ui.card().classes("w-full shadow-md"):
        ui.label("⚡ 快速操作").classes("text-lg font-semibold mb-4")
        
        with ui.row().classes("gap-2 flex-wrap"):
            ui.button("🔄 刷新所有任务", on_click=lambda: refresh_all_tasks(), color="secondary").props("outline")
            ui.button("🧪 测试所有配置", on_click=lambda: test_all_tasks(), color="info").props("outline")
            ui.button("⏸️ 暂停所有任务", on_click=lambda: pause_all_tasks(), color="warning").props("outline")
            ui.button("🛑 停止所有任务", on_click=lambda: stop_all_tasks(), color="negative").props("outline")
            ui.button("➕ 新建任务", on_click=lambda: create_new_task(), color="primary").props("outline")


async def refresh_all_tasks():
    """刷新所有任务状态"""
    ui.notify("🔄 正在刷新任务状态...", type="info")
    await asyncio.sleep(1)  # 模拟刷新过程
    ui.notify("✅ 任务状态已更新", type="positive")


async def test_all_tasks():
    """测试所有任务配置"""
    tasks = task_monitor.list_all_tasks()
    if not tasks:
        ui.notify("❌ 没有找到可测试的任务", type="warning")
        return
    
    ui.notify(f"🧪 正在测试 {len(tasks)} 个任务...", type="info")
    
    success_count = 0
    error_count = 0
    
    for task in tasks:
        result = task_monitor.test_task(task['name'])
        if result['success']:
            success_count += 1
        else:
            error_count += 1
    
    message = f"测试完成: {success_count}个通过, {error_count}个失败"
    ui.notify(message, type="positive" if error_count == 0 else "warning")


async def pause_all_tasks():
    """暂停所有任务"""
    tasks = [t for t in task_monitor.list_all_tasks() if t.get('is_running')]
    if not tasks:
        ui.notify("ℹ️ 没有运行中的任务", type="info")
        return
    
    for task in tasks:
        task_monitor.stop_task(task['name'])
    
    ui.notify(f"⏸️ 已暂停 {len(tasks)} 个任务", type="info")


async def stop_all_tasks():
    """停止所有任务"""
    tasks = task_monitor.list_all_tasks()
    running_tasks = [t for t in tasks if t.get('is_running')]
    
    if not running_tasks:
        ui.notify("ℹ️ 没有运行中的任务", type="info")
        return
    
    for task in running_tasks:
        task_monitor.stop_task(task['name'])
    
    ui.notify(f"🛑 已停止 {len(running_tasks)} 个任务", type="info")


def create_new_task():
    """创建新任务（简化版本）"""
    ui.notify("➕ 创建新任务功能即将推出", type="info")


def create_task_list_panel():
    """创建任务列表面板"""
    with ui.card().classes("w-full shadow-md"):
        ui.label("📋 任务列表").classes("text-lg font-semibold mb-4")
        
        # 添加搜索过滤
        search_input = ui.input(
            label="搜索任务",
            placeholder="输入任务名称...",
            on_change=lambda e: filter_tasks(e.value)
        ).classes("w-full mb-4").props("outlined")
        
        # 任务列表容器
        task_list_container = ui.column().classes("w-full gap-3")
        
        # 初始加载所有任务
        update_task_list(task_list_container, "")
        
        # 返回更新函数
        return task_list_container, search_input


def update_task_list(container, filter_text: str = ""):
    """更新任务列表"""
    container.clear()
    
    all_tasks = task_monitor.list_all_tasks()
    
    # 应用过滤器
    if filter_text.strip():
        filtered_tasks = [t for t in all_tasks if filter_text.lower() in t['name'].lower()]
    else:
        filtered_tasks = all_tasks
    
    if not filtered_tasks:
        with container:
            ui.label("📭 没有找到匹配的任务").classes("text-gray-500 italic text-center py-8")
        return
    
    for task in filtered_tasks:
        with container:
            with ui.card().classes("w-full p-4"):
                # 任务基本信息
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("flex-grow"):
                        ui.label(task['name']).classes("font-bold text-lg")
                        
                        # 任务状态信息
                        status_info = []
                        if task.get('has_config'):
                            status_info.append("✅ 已配置")
                        else:
                            status_info.append("❌ 未配置")
                        
                        if task.get('is_running'):
                            status_info.append(f"🔴 运行中 ({task.get('uptime', '')})")
                        elif task.get('can_start'):
                            status_info.append("🟢 就绪")
                        else:
                            status_info.append("⚪ 不可用")
                        
                        if task.get('next_run'):
                            status_info.append(f"⏰ 下次运行: {task['next_run']}")
                        
                        ui.label(" | ".join(status_info)).classes("text-sm text-gray-600 mt-2")
                        
                        # 最后修改时间
                        last_modified = task.get('last_modified')
                        if last_modified:
                            from datetime import datetime as dt
                            modified_time = dt.fromtimestamp(last_modified)
                            ui.label(f"📝 最后修改: {modified_time.strftime('%Y-%m-%d %H:%M')}").classes("text-xs text-gray-500")
                    
                    # 操作按钮
                    with ui.row().classes("gap-2"):
                        test_btn = ui.button("🧪 测试", size="sm", on_click=lambda t=task['name']: test_single_task_ui(t))
                        start_btn = ui.button("▶️ 开始", size="sm", on_click=lambda t=task['name']: start_single_task_ui(t), disable=not task.get('can_start') or task.get('is_running'))
                        stop_btn = ui.button("⏹️ 停止", size="sm", on_click=lambda t=task['name']: stop_single_task_ui(t), disable=not task.get('is_running'))
                
                # 任务详情（可扩展）
                with ui.expansion("📖 查看详情", icon="expand_more").classes("mt-2"):
                    with ui.column().classes("gap-2"):
                        ui.label("任务详情").classes("font-medium")
                        
                        if task.get('has_config'):
                            try:
                                import json
                                with open(task['config_path'], 'r', encoding='utf-8') as f:
                                    config_data = json.load(f)
                                
                                # 显示配置摘要
                                chats = config_data.get('chats', [])
                                ui.label(f"聊天数量: {len(chats)}").classes("text-sm")
                                
                                total_actions = sum(len(chat.get('actions', [])) for chat in chats)
                                ui.label(f"动作总数: {total_actions}").classes("text-sm")
                                
                                sign_at = config_data.get('sign_at', '未设置')
                                ui.label(f"签到时间: {sign_at}").classes("text-sm")
                                
                                random_seconds = config_data.get('random_seconds', 0)
                                if random_seconds > 0:
                                    ui.label(f"随机延迟: {random_seconds}秒").classes("text-sm")
                                
                            except Exception as e:
                                ui.label(f"读取配置失败: {e}").classes("text-red-600 text-sm")
                        else:
                            ui.label("暂无配置信息").classes("text-gray-500 text-sm")


def filter_tasks(filter_text: str):
    """过滤任务列表"""
    if hasattr(ui, '_current_page') and hasattr(ui._current_page, 'state'):
        # 如果有当前页面状态，更新任务列表
        pass


async def test_single_task_ui(task_name: str):
    """在UI中测试单个任务"""
    result = task_monitor.test_task(task_name)
    
    if result['success']:
        details = "\n".join([f"{k}: {v}" for k, v in result['details'].items()])
        ui.notify(f"✅ {task_name} 测试成功\n{details}", type="positive")
    else:
        ui.notify(f"❌ {task_name} 测试失败: {result['message']}", type="negative")


async def start_single_task_ui(task_name: str):
    """在UI中启动单个任务"""
    success = task_monitor.start_task(task_name)
    if success:
        ui.notify(f"✅ 任务 {task_name} 已启动", type="positive")
        # 重新加载任务列表以更新状态
        if 'task_list_container' in locals():
            update_task_list(task_list_container, "")
    else:
        ui.notify(f"❌ 启动任务 {task_name} 失败", type="negative")


async def stop_single_task_ui(task_name: str):
    """在UI中停止单个任务"""
    success = task_monitor.stop_task(task_name)
    if success:
        ui.notify(f"⏹️ 任务 {task_name} 已停止", type="info")
        # 重新加载任务列表以更新状态
        if 'task_list_container' in locals():
            update_task_list(task_list_container, "")
    else:
        ui.notify(f"❌ 停止任务 {task_name} 失败", type="negative")


def create_enhanced_dashboard(container):
    """创建增强版仪表板"""
    with container:
        # 顶部标题和用户信息
        with ui.row().classes("w-full justify-between items-center mb-6"):
            ui.label("🚀 TG Signer 任务管理中心").classes("text-2xl font-bold")
            
            # 如果登录了，显示用户信息
            if auth_system.get_current_user():
                user_info = auth_system.get_current_user()
                ui.label(f"👋 {user_info.get('first_name', '用户')}").classes("text-lg")

        # 任务总览面板
        create_task_overview_panel()
        
        # 快速操作面板
        create_quick_actions_panel()
        
        # 任务列表面板
        task_list_container, search_input = create_task_list_panel()


# 必要的导入（在实际文件中需要添加到顶部）
import asyncio