# Tajido-Auto

塔吉多网页自动化助手，基于 Playwright 实现自动发帖、自动回复评论、自动浏览点赞。

Tajido web automation assistant powered by Playwright. It supports auto posting, auto replying to comments, and auto browsing with likes.

## 功能特性 / Features

- tkinter 图形界面，实时展示运行日志
- 持久化浏览器上下文，自动保存登录状态
- 自动发帖（支持纯文本，可选图片）
- 自动检查并回复新评论
- 自动浏览帖子并点赞（可设置点赞数量和最长运行时间）

## 项目结构 / Project Structure

- `gui.py`: 图形界面入口（推荐）
- `main.py`: 脚本入口（命令行模式）
- `core/auth_manager.py`: 浏览器上下文初始化、登录态持久化
- `core/post_manager.py`: 发帖流程
- `core/interaction_manager.py`: 回复评论、浏览点赞流程
- `utils/config.py`: 基础配置（目标网址等）
- `utils/selectors.py`: 页面选择器集中配置
- `utils/logger.py`: 控制台 + 文件日志
- `runtime/`: 本地运行日志与错误截图
- `assets/`: 示例素材目录

## 环境要求 / Requirements

- Python 3.13.2
- Playwright 依赖（见 `requirements.txt`）
- Chromium 浏览器（通过 Playwright 安装）

## 安装步骤 / Installation

### Windows 示例 / Windows example

```batch
git clone https://github.com/Rezetyan/Tajido-Auto.git
cd Tajido-Auto
python -m venv venv
CALL venv\Scripts\activate.bat
pip install -r requirements.txt
playwright install chromium
```

### macOS / Linux 示例 / macOS / Linux example

```bash
git clone https://github.com/Rezetyan/Tajido-Auto.git
cd Tajido-Auto
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 运行方式 / How To Run

### 安全演练模式 / Dry-run mode

推荐首次使用先开启 dry-run。该模式会执行页面导航、元素识别和计数，但不会提交帖子、发送回复、点击点赞，也不会选择图片上传。

Windows PowerShell:

```powershell
$env:TAJIDO_DRY_RUN="1"
python gui.py
```

命令行模式同样支持：

```powershell
$env:TAJIDO_DRY_RUN="1"
python main.py
```

### GUI 模式（推荐） / GUI mode (recommended)

```bash
python gui.py
```

首次运行流程：

1. 点击“初始化 / 登录浏览器”
2. 在弹出的浏览器中手动登录塔吉多
3. 建议先保持 Dry-run 勾选，确认日志显示能找到目标元素
4. 确认无误后再取消 Dry-run，使用发帖、回复、点赞按钮

### 脚本模式 / Script mode

```bash
python main.py
```

`main.py` 中任务调用默认是注释状态，请按需取消注释后运行。

脚本模式也会读取 `TAJIDO_DRY_RUN` 环境变量；真实执行前请先用 dry-run 验证选择器命中情况。

## 配置说明 / Configuration

- 目标站点地址：`utils/config.py` 中 `TARGET_URL`
- 回复检查入口：`utils/config.py` 中 `REPLY_URL`，也可通过 `TAJIDO_REPLY_URL` 环境变量覆盖
- 页面选择器：`utils/selectors.py`
- 自动发帖默认版区：`异环 / 「呗果」揭示板`，由 `core/post_manager.py` 的 `create_post()` 参数控制
- GUI 默认目标链接：`gui.py` 中目标链接输入框默认值
- 可选发帖图片：默认读取 `assets/sample.png`（不存在则仅发文本）

## 运行产物 / Runtime Artifacts

- `browser_data/`: 浏览器登录态与本地缓存
- `runtime/tajido.log`: 运行日志
- `runtime/screenshots/`: 错误截图

这些文件用于本地运行，已在 `.gitignore` 中排除，不会上传到 GitHub。

## 测试 / Tests

项目包含无副作用的本地 fixture 测试，不访问真实网站、不发帖、不回复、不点赞。

```powershell
python -m unittest discover -v
python -m compileall main.py gui.py core utils tests
```

## 注意事项 / Notes

- 自动化依赖页面结构与选择器，若网站前端改版可能需要更新 `core/` 下选择器。
- 发帖、回复、点赞都属于真实账号副作用操作。请先用 dry-run 验证，再手动确认网站条款、账号状态和选择器命中情况。
- 请在遵守目标网站服务条款和适用法律的前提下使用本项目。
