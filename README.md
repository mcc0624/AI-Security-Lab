# AI+安全实训 - 简易用户信息管理平台

四川大学网络空间安全学院 2025级 AI+安全实训项目

## 项目简介

本项目是一个**简易用户信息管理平台**，使用 Flask 框架构建，作为《AI+安全》实训课程的统一成品项目。项目采用"AI 生成代码 + 漏洞自然暴露 + 安全修复"的教学模式，覆盖 10 类核心网络安全漏洞。

## 项目结构

```
ai-security-lab/
├── core/                    # 🔒 核心功能模块（含漏洞）
│   ├── auth.py              # Day 2: 密码泄露
│   ├── database.py          # Day 3: SQL 注入
│   ├── file_handler.py      # Day 4: 任意文件上传
│   ├── user_service.py      # Day 5: 越权/支付漏洞
│   ├── page_loader.py       # Day 6: 文件包含
│   ├── password_manager.py  # Day 7: CSRF
│   ├── url_fetcher.py       # Day 8: SSRF
│   ├── command_runner.py    # Day 9: 命令注入
│   └── xml_processor.py     # Day 10: XXE
├── templates/               # 🎨 HTML 模板（可自由修改）
├── static/                  # 🎨 CSS/JS 文件（可自由修改）
│   ├── css/style.css
│   └── js/app.js
├── fix/                     # 📝 学生修复代码存放目录
├── pages/                   # 📄 动态加载的页面文件
├── app.py                   # 主应用入口
├── verify.py                # 验证脚本
└── requirements.txt         # Python 依赖
```

## 启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动应用
python app.py

# 3. 访问
# http://127.0.0.1:5000
# 默认账号: admin / admin123
```

## 课程安排

| 天数  | 功能模块     | 漏洞类型     | 核心文件              |
|-------|-------------|-------------|----------------------|
| Day 2 | 登录/注册   | 密码泄露     | core/auth.py         |
| Day 3 | 数据库操作   | SQL 注入     | core/database.py     |
| Day 4 | 文件上传     | 任意文件上传  | core/file_handler.py |
| Day 5 | 个人中心/充值| 越权/支付漏洞 | core/user_service.py |
| Day 6 | 页面加载     | 文件包含     | core/page_loader.py  |
| Day 7 | 密码修改     | CSRF         | core/password_manager.py |
| Day 8 | URL 请求     | SSRF         | core/url_fetcher.py  |
| Day 9 | Ping 测试    | 命令注入     | core/command_runner.py |
| Day 10| XML 导入     | XXE          | core/xml_processor.py |

## 重要规则

- **core/** 目录为锁定代码，包含教学用安全漏洞，请勿修改
- 修复代码请写在 **fix/** 目录中
- **templates/** 和 **static/** 可以自由修改和美化
