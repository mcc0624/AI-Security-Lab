# Day 9 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-09 -- core/command_runner.py
④ 运行 python app.py，测试命令注入漏洞
⑤ 修复：修复代码写入 fix/command_runner_fix.py
⑥ 提交：git add -A && git commit -m "day-09: Ping功能 + 命令注入修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、上传、个人中心、页面加载、密码修改、URL抓取功能。
> 请帮我完成以下功能：
>
> **Day 9 - Ping 网络诊断功能**
>
> 1. 生成一个 Ping 测试页面（templates/ping.html），包含 IP 地址输入框和"Ping"按钮
> 2. 在 app.py 中添加 Ping 路由（/ping），POST 方式提交 IP 地址
> 3. 执行结果用控制台风格（黑色背景、绿色文字）显示
> 4. 在导航栏添加"Ping测试"链接（登录后显示）
> 5. 超时时间为 30 秒
> 6. 风格统一
>
> 生成完成后告诉我，我会导入命令执行核心模块来让功能真正运行。
