# AI+安全实训 - 课程文档索引

## 目录

| 天数 | 主题 | 漏洞类型 | 文档 |
|------|------|---------|------|
| Day 1 | 环境搭建 | — | [day-01-environment.md](day-01-environment.md) |
| Day 2 | 用户登录 | 密码泄露 | [day-02-password-leak.md](day-02-password-leak.md) |
| Day 3 | 数据库操作 | SQL 注入 | [day-03-sql-injection.md](day-03-sql-injection.md) |
| Day 4 | 文件上传 | 任意文件上传 | [day-04-file-upload.md](day-04-file-upload.md) |
| Day 5 | 个人中心/充值 | 越权/支付漏洞 | [day-05-privilege-escalation.md](day-05-privilege-escalation.md) |
| Day 6 | 页面加载 | 文件包含 (LFI) | [day-06-file-inclusion.md](day-06-file-inclusion.md) |
| Day 7 | 密码修改 | CSRF | [day-07-csrf.md](day-07-csrf.md) |
| Day 8 | URL 请求 | SSRF | [day-08-ssrf.md](day-08-ssrf.md) |
| Day 9 | Ping 测试 | 命令注入 | [day-09-command-injection.md](day-09-command-injection.md) |
| Day 10 | XML 导入 | XXE | [day-10-xxe.md](day-10-xxe.md) |

## 每个文档包含的内容

1. **页面部署提示词** — 发给 Claude 生成带漏洞功能的 Prompt
2. **漏洞关键代码解释** — 逐行分析存在漏洞的代码
3. **漏洞成因总结** — 为什么会出现这个漏洞
4. **POC 代码** — 可直接运行的漏洞利用命令
5. **POC 代码测试方法** — Burp Suite + 手动测试步骤
6. **POC 代码详细解释** — 每一条命令/参数的作用
7. **修复方案** — 安全编码的修复代码
8. **课后作业** — 学生独立完成的练习
