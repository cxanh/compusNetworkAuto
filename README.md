# 长沙学院校园网自动登录

本项目用于自动登录 `http://10.0.100.3/` 校园网门户。

- 首次运行可配置账号密码
- 后续一键自动登录
- 支持运营商选择（校园网/中国联通/中国移动/中国电信）
- 提供网页配置面板（美观 UI）

## 目录说明

- `auto_login_csxy.py`：主脚本（命令行登录）
- `web_app.py`：Flask 网页配置与执行入口
- `templates/index.html`、`static/app.css`：前端页面
- `start_auto_login.bat`：双击执行命令行登录
- `start_web_ui.bat`：双击启动 Web 配置页
- `campus_login_config.json`：本地配置文件（首次保存后生成）
- `tools/chromedriver/.../chromedriver.exe`：本地驱动（可选）

## 环境要求

1. Windows + Python 3.8+
2. Google Chrome
3. Python 依赖：`selenium`、`Flask`

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

## 命令行方式

### 首次配置

```powershell
python auto_login_csxy.py --init
```

按提示填写：账号、密码、运营商、地址、驱动路径等。

### 日常运行

```powershell
python auto_login_csxy.py
```

或双击：`start_auto_login.bat`

## 网页方式（推荐）

### 启动

```powershell
python web_app.py
```

或双击：`start_web_ui.bat`

浏览器访问：`http://127.0.0.1:5050`

### 功能

1. 输入并保存账号、密码、运营商、URL、驱动路径
2. 配置无头模式/截图保存
3. 点击“立即登录并检测”直接调用登录流程
4. 页面显示执行日志与状态提示

## 配置文件示例

`campus_login_config.json`：

```json
{
  "username": "你的账号",
  "password": "你的密码",
  "url": "http://10.0.100.3/",
  "chromedriver_path": "C:\\Tools\\chromedriver\\chromedriver-win64\\chromedriver.exe",
  "isp_keyword": "中国联通",
  "headless": true,
  "save_screenshots": true
}
```

`isp_keyword` 常用值：

- `中国联通`
- `校园网`
- `中国移动`
- `中国电信`

## 常见问题

1. 报错 `chromedriver 不存在`
- 检查 `chromedriver_path` 是否正确
- 或留空让 Selenium 自动匹配

2. 页面状态异常/误判
- 查看 `01_open_page.png`、`02_after_submit.png`、`03_final.png`
- 查看 `debug_unknown_state.html`

3. Chrome 与 chromedriver 不兼容
- 保证主版本一致（例如都为 145）

## 安全提示

- `campus_login_config.json` 含明文密码，仅建议保存在个人设备。
- 不要将该文件提交到公开仓库。
