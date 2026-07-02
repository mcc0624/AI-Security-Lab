# Day 1 - 环境搭建与工具部署

## 一、概述

第一天不涉及漏洞，目标是搭建完整的开发和安全测试环境。

## 二、环境需求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10+ / Kali Linux |
| 内存 | ≥ 16GB |
| 硬盘 | ≥ 80GB 可用空间 |
| Python | ≥ 3.10 |

## 三、安装清单

1. **Python** — 运行 Flask 应用
2. **Git** — 版本控制和项目下载
3. **Claude Code** — AI 编码助手
4. **Burp Suite Community** — Web 抓包工具
5. **SQLMap** — SQL 注入自动化工具

## 四、验证环境

```bash
python --version
git --version
pip --version
```

## 五、项目部署

```bash
git clone https://github.com/mcc0624/AI-Security-Lab.git
cd AI-Security-Lab
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000
```
