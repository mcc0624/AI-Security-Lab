# AI+安全实训 - 简易用户信息管理平台

四川大学网络空间安全学院 2025级 AI+安全实训项目

## 项目简介

本项目是一个**简易用户信息管理平台**，使用 Flask 框架构建，作为《AI+安全》实训课程的统一成品项目。项目采用"AI 生成代码 + 漏洞自然暴露 + 安全修复"的教学模式，覆盖 10 类核心网络安全漏洞。

## 🚀 快速开始（两种方式）

### 方式一：使用 Skill（推荐，无需下载仓库）

> **适用场景**：学生已有 Claude Code 环境，希望一步到位

1. 在任意工作目录下，运行 Claude Code
2. 输入 `/ai-security-lab`
3. Claude 会自动创建项目并写入所有代码（包括含漏洞的核心模块）
4. 按提示启动应用，开始每日实训

> **安装 Skill**：将 `.claude/skills.json` 的内容合并到你的 Claude Code 配置中即可。

### 方式二：克隆仓库

```bash
git clone <仓库地址>
cd ai-security-lab
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000
# 默认账号: admin / admin123
```

---

## 📁 项目结构

```
ai-security-lab/
├── core/                    # 🔒 核心功能模块（含漏洞，禁止修改）
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
├── fix/                     # 📝 学生修复代码存放目录
├── pages/                   # 动态加载的页面文件
├── .claude/                 # Claude Code 配置（含 Skill 定义）
├── app.py                   # 主应用入口
├── verify.py                # core/ 完整性验证
└── requirements.txt         # Python 依赖
```

## 📅 课程安排

| 天数 | 新增功能 | 漏洞类型 | 核心文件 |
|------|---------|----------|---------|
| Day 1 | 环境搭建 | — | Kali / Burp Suite / PyCharm |
| Day 2 | 用户登录 | 密码泄露 | core/auth.py |
| Day 3 | 数据库 / 搜索 | SQL 注入 | core/database.py |
| Day 4 | 头像上传 | 任意文件上传 | core/file_handler.py |
| Day 5 | 个人中心 / 充值 | 越权 + 支付漏洞 | core/user_service.py |
| Day 6 | 动态页面加载 | 文件包含 (LFI/RFI) | core/page_loader.py |
| Day 7 | 密码修改 | CSRF | core/password_manager.py |
| Day 8 | URL 抓取 | SSRF | core/url_fetcher.py |
| Day 9 | Ping 测试 | 命令注入 | core/command_runner.py |
| Day 10 | XML 导入 | XXE | core/xml_processor.py |

## 🔒 重要规则

| 规则 | 说明 |
|------|------|
| **core/ 不可修改** | 包含教学用漏洞代码，修改后漏洞消失将影响学习 |
| **修复写在 fix/** | 在 fix/ 目录创建修复版本，再修改 app.py 引用 |
| **UI 自由发挥** | templates/ 和 static/ 可以完全自定义样式和交互 |
| **每日提交日志** | 运行 `python verify.py` 验证 core/ 完整性后提交 |

## 🔧 每日常规流程

```mermaid
graph LR
    A[拉取/进入项目] --> B[阅读当天 core/ 模块]
    B --> C[发现漏洞]
    C --> D[用 Burp Suite 复现]
    D --> E[在 fix/ 编写修复]
    E --> F[验证修复通过]
    F --> G[撰写攻防日志]
```

## ⚠️ 漏洞一览

| # | 漏洞 | 复现 Payload |
|---|------|-------------|
| 1 | 硬编码凭据 | 查看 HTML 注释、JS 源码 |
| 2 | 明文密码存储 | 登录响应中直接包含密码字段 |
| 3 | SQL 注入 | `admin' OR '1'='1` |
| 4 | 任意文件上传 | 上传 .py 文件获取 Webshell |
| 5 | 水平越权 | `GET /profile?user_id=2` |
| 6 | 支付漏洞 | `amount=-10000` |
| 7 | 文件包含 | `GET /page?name=../../etc/passwd` |
| 8 | CSRF | 恶意页面自动提交密码修改 |
| 9 | SSRF | `url=file:///etc/passwd` |
| 10 | 命令注入 | `127.0.0.1;id` |
| 11 | XXE | `<!ENTITY xxe SYSTEM "file:///etc/passwd">` |

## 📤 提交成果

- 每日 22:00 前提交《每日攻防日志》
- 日志包含：漏洞代码截图、复现步骤、修复方案、成员分工
- 第 9-10 天整合为《项目漏洞攻防总报告》
- 最终答辩需提交双版本代码库（vulnerable + secure）和 PPT
