# AI+安全实训 - 简易用户信息管理平台

四川大学网络空间安全学院 2025级 AI+安全实训项目

## 仓库分支说明

本项目按天分分支，**每天只包含当天及之前的功能代码**：

| 分支 | 对应天数 | 包含功能 |
|------|---------|---------|
| `master` 或 `base` | — | 基础框架（空项目骨架） |
| `day-02` | Day 2 | 用户登录（密码泄露） |
| `day-03` | Day 3 | + 数据库、注册、搜索（SQL注入） |
| `day-04` | Day 4 | + 文件上传 |
| `day-05` | Day 5 | + 个人中心、充值（越权/支付漏洞） |
| `day-06` | Day 6 | + 动态页面加载（文件包含） |
| `day-07` | Day 7 | + 密码修改（CSRF） |
| `day-08` | Day 8 | + URL抓取（SSRF） |
| `day-09` | Day 9 | + Ping测试（命令注入） |
| `day-10` | Day 10 | + XML导入（XXE） |
| `full-version` | 全部 | 包含全部功能的完整参考版本 |

## 学生操作流程

```bash
# 第一天：克隆项目
git clone https://github.com/mcc0624/AI-Security-Lab.git
cd AI-Security-Lab
pip install -r requirements.txt

# 切换到当前天数对应的分支
git checkout day-02

# 打开 Claude Code 开始实训
claude /ai-security-lab
```

## 规则

- **core/** 目录为锁定代码，禁止修改
- 修复代码请写在 **fix/** 目录中
- **templates/** 和 **static/** 可以自由修改
