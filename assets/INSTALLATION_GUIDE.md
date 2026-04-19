# TG Signer 增强版 - 安装和部署指南

## 📋 目录

1. [系统要求](#system-requirements)
2. [快速安装](#quick-install)
3. [手动安装](#manual-installation)
4. [Docker部署](#docker-deployment)
5. [环境配置](#environment-configuration)
6. [故障排除](#troubleshooting)

---

## 🖥️ 系统要求

### 最低配置
- **操作系统**: Linux/macOS/Windows (WSL2)
- **Python版本**: 3.10+
- **内存**: 至少2GB可用RAM
- **磁盘空间**: 100MB可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **CPU**: 双核2GHz以上
- **内存**: 4GB+ RAM
- **磁盘**: SSD存储，500MB+空间
- **网络**: 宽带连接

---

## 🚀 快速安装

### 方法一：一键安装脚本（推荐）

```bash
cd /vol2/1000/Claw/tg-signer-revamp
chmod +x install.sh
./install.sh
```

**安装脚本功能**:
- 自动检测Python版本
- 创建虚拟环境
- 安装所有依赖包
- 验证安装结果
- 启动WebUI测试

### 方法二：手动安装

```bash
# 1. 克隆或进入项目目录
cd /vol2/1000/Claw/tg-signer-revamp

# 2. 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 3. 安装核心依赖
pip install click pydantic croniter json_repair typing-extensions httpx

# 4. 安装GUI依赖
pip install nicegui fastapi starlette uvicorn aiohttp

# 5. 安装可选优化包
pip install tgcrypto  # 提升Telegram连接速度

# 6. 安装项目
pip install -e .
```

---

## 🐳 Docker部署

### 构建镜像

```bash
# 构建基础镜像
docker build -t tg-signer-enhanced .

# 构建带GUI的镜像
docker build --build-arg GUI=true -t tg-signer-enhanced-gui .
```

### 运行容器

```bash
# 基础运行（无GUI）
docker run -d \
  --name tg-signer \
  -p 8080:8080 \
  -v /path/to/data:/app/.signer \
  -e TG_API_ID=your_api_id \
  -e TG_API_HASH=your_api_hash \
  tg-signer-enhanced

# 带GUI的运行
docker run -d \
  --name tg-signer-gui \
  -p 8080:8080 \
  -v /path/to/data:/app/.signer \
  -e TG_API_ID=your_api_id \
  -e TG_API_HASH=your_api_hash \
  -e GUI=true \
  tg-signer-enhanced-gui
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  tg-signer:
    image: tg-signer-enhanced
    container_name: tg-signer
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/.signer
    environment:
      - TG_API_ID=${TG_API_ID}
      - TG_API_HASH=${TG_API_HASH}
      - TG_PROXY=${TG_PROXY:-}
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # 如果需要数据库持久化
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: tg_signer
      POSTGRES_USER: signer
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pg_data:
```

---

## ⚙️ 环境配置

### Telegram API设置

```bash
# 获取API凭证
export TG_API_ID=your_api_id
export TG_API_HASH=your_api_hash

# 可选：代理设置
export TG_PROXY=socks5://127.0.0.1:1080
```

**获取API密钥**: https://my.telegram.org

### WebUI认证配置

```bash
# 设置访问密码（可选但推荐）
export TG_SIGNER_GUI_AUTHCODE=your_complex_password_here

# 自定义端口
export NICEGUI_PORT=9000

# 工作目录
export TG_SIGNER_WORKDIR=/custom/workdir
```

### 日志配置

```bash
# 日志级别
export TG_SIGNER_LOG_LEVEL=info

# 日志文件路径
export TG_SIGNER_LOG_FILE=/var/log/tg-signer.log

# 日志轮转
export TG_SIGNER_LOG_ROTATE_SIZE=100MB
export TG_SIGNER_LOG_MAX_FILES=10
```

---

## 🔧 配置文件

### 主配置文件

```yaml
# config.yaml (可选)
app:
  port: 8080
  host: 0.0.0.0
  debug: false

telegram:
  api_id: ${TG_API_ID}
  api_hash: ${TG_API_HASH}
  proxy: ${TG_PROXY}

logging:
  level: info
  file: logs/tg-signer.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

webui:
  auth_code: ${TG_SIGNER_GUI_AUTHCODE}
  session_timeout: 3600
  max_login_attempts: 5
```

### 任务配置文件示例

```json
{
  "chats": [
    {
      "chat_id": -100123456789,
      "message_thread_id": null,
      "name": "签到群组",
      "delete_after": 300,
      "actions": [
        {
          "action": 1,
          "text": "签到"
        },
        {
          "action": 2,
          "dice": "🎲"
        }
      ],
      "action_interval": 2.0
    }
  ],
  "sign_at": "0 6 * * *",
  "random_seconds": 300,
  "sign_interval": 60
}
```

---

## 🧪 测试和验证

### 单元测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试模块
pytest tests/test_core.py

# 生成测试覆盖率报告
pytest --cov=tg_signer tests/
```

### 集成测试

```bash
# 启动测试服务
python -m pytest tests/integration/

# WebUI端到端测试
python -m pytest tests/e2e/
```

### 性能测试

```bash
# 基准测试
python -m pytest tests/benchmark/

# 压力测试
locust -f tests/stress_test.py
```

---

## 📦 依赖管理

### requirements.txt

```txt
# 核心依赖
click>=8.0
pydantic>=2.0
croniter>=1.3
json_repair>=0.4
typing-extensions>=4.0
httpx>=0.23

# GUI依赖
nicegui>=1.0
fastapi>=0.95
starlette>=0.26
uvicorn[standard]>=0.21

# 可选优化
tgcrypto>=1.2  # Telegram加密加速
psutil>=5.8    # 系统监控
watchdog>=2.1  # 文件系统监控

# 开发依赖
pytest>=7.0
pytest-asyncio>=0.18
ruff>=0.0.260  # 代码格式化
```

### dev-requirements.txt

```txt
-r requirements.txt

# 开发工具
black>=22.0
isort>=5.10
mypy>=0.991
flake8>=5.0

# 测试工具
pytest-cov>=4.0
pytest-mock>=3.10
factory-boy>=3.2

# 文档工具
sphinx>=5.0
autodoc>=0.5
```

---

## 🛠️ 故障排除

### 常见问题解决

#### 1. 安装失败

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决方案**:
```bash
# 清理缓存重新安装
pip cache purge
pip install --no-cache-dir -e .

# 或者使用完整依赖列表
pip install -r requirements.txt
```

#### 2. WebUI无法启动

**错误**: `AttributeError: module 'nicegui' has no attribute 'run'`

**解决方案**:
```bash
# 升级NiceGUI
pip install --upgrade nicegui

# 检查版本兼容性
nicegui --version
python -c "import nicegui; print(nicegui.__version__)"
```

#### 3. Telegram登录问题

**错误**: `Connection refused` or `Authentication failed`

**解决方案**:
```bash
# 检查网络连接
ping api.telegram.org

# 验证API设置
echo $TG_API_ID
echo $TG_API_HASH

# 测试连接
curl -v https://api.telegram.org
```

#### 4. 性能问题

**症状**: WebUI响应缓慢或卡顿

**解决方案**:
```bash
# 监控系统资源
htop
df -h
free -m

# 增加资源限制
ulimit -n 65536  # 文件描述符
ulimit -u 65536  # 进程数

# 优化配置
export NICEGUI_RELOAD=false
export UVICORN_WORKERS=4
```

---

## 🔒 安全最佳实践

### 生产环境配置

```bash
# 禁用调试模式
export TG_SIGNER_DEBUG=false

# 强认证密码
export TG_SIGNER_GUI_AUTHCODE=$(openssl rand -base64 32)

# HTTPS反向代理
export NGINX_SSL=true
export NGINX_CERT_PATH=/etc/ssl/certs/tg-signer.crt
export NGINX_KEY_PATH=/etc/ssl/private/tg-signer.key
```

### 权限管理

```bash
# 创建专用用户
sudo useradd -r -s /bin/false tg-signer

# 设置数据目录权限
sudo chown -R tg-signer:tg-signer /opt/tg-signer/.signer
sudo chmod 750 /opt/tg-signer/.signer

# 防火墙规则
sudo ufw allow 8080/tcp
sudo ufw deny from any to any port 8080 proto tcp
```

---

## 📈 监控和维护

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/api/health

# 查看日志
tail -f logs/tg-signer.log

# 监控资源使用
watch -n 1 'ps aux | grep python; df -h; free -m'
```

### 备份策略

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backup/tg-signer"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份配置
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" .signer/

# 备份数据库
cp .signer/data.sqlite3 "$BACKUP_DIR/db_$DATE.sqlite3"

# 清理旧备份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.sqlite3" -mtime +30 -delete
```

---

## 📞 技术支持

如遇问题，请按照以下步骤排查:

1. **查看日志**: `cat logs/tg-signer.log`
2. **检查配置**: `printenv | grep TG_`
3. **运行测试**: `python -m pytest tests/unit/`
4. **搜索Issues**: 查看GitHub Issues

**联系信息**:
- GitHub Issues: https://github.com/your-repo/issues
- 邮件支持: support@tg-signer.com
- 社区论坛: https://community.tg-signer.com

---

*最后更新*: 2024年
*维护团队*: TG Signer 增强项目组
*文档版本*: v1.0.0