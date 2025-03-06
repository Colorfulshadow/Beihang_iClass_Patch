# BUAA iClass Attendance System

这是一个北航 iClass 自动签到系统，可以自动登录、获取当天的课程信息，并生成签到二维码。

## 特性

- 自动登录北航 SSO 系统
- 获取当前学期所有课程信息
- 获取当天需要考勤的课程
- 为每门课程生成签到二维码
- 自动刷新二维码以保持时效性

## 项目结构

```
buaa-iclass-attendance/
├── app.py                  # 主 Flask 应用
├── requirements.txt        # Python 依赖
├── config.py               # 配置文件（SSO 凭据等）
├── static/                 # 静态文件
│   └── css/
│       └── style.css
├── templates/              # HTML 模板
│   └── index.html          # 主页面
└── utils/                  # 工具模块
    ├── __init__.py
    ├── auth.py             # 认证模块
    ├── courses.py          # 课程信息模块
    └── qrcode.py           # 二维码生成模块
```

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

编辑 `config.py` 文件，填入你的 SSO 凭据：

```python
# SSO Credentials
USERNAME = "你的用户名"  # 例如 21374401
PASSWORD = "你的密码"    # SSO 系统的密码
```

### 3. 运行

```bash
python app.py
```

然后在浏览器中访问 `http://localhost:5000`。

## 使用方法

1. 打开网页后，输入你的 SSO 用户名和密码登录（如果没有在 config.py 中设置）
2. 系统会自动获取当天需要考勤的课程，并为每门课生成签到二维码
3. 二维码会自动刷新，确保时效性
4. 你可以调整二维码刷新频率
5. 如需手动刷新课程信息，点击"刷新课程"按钮

## 注意事项

- 本工具仅用于学习和研究目的，请勿用于实际逃课
- 请保管好你的账户信息，不要将包含账户信息的配置文件分享给他人
- 本工具不会记录或传输你的账户信息到除北航官方系统以外的任何地方