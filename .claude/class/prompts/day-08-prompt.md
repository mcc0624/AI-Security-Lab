# Day 8 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-08 -- core/url_fetcher.py
④ 运行 python app.py，测试 SSRF 服务端请求伪造漏洞
⑤ 修复：修复代码写入 fix/url_fetcher_fix.py
⑥ 提交：git add -A && git commit -m "day-08: URL抓取 + SSRF修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、上传、个人中心、页面加载、密码修改功能。
> 请帮我完成以下功能：
>
> **Day 8 - URL 抓取功能**
>
> 1. 在 app.py 中添加 URL 抓取路由（/fetch-url），POST 方式提交 URL
> 2. 在首页添加 URL 抓取的入口和一个 URL 输入框
> 3. 抓取成功后显示：状态码、响应头、响应内容前 5000 字符
> 4. 抓取失败时显示错误信息
> 5. 风格统一
>
> 生成完成后告诉我，我会导入 URL 请求核心模块来让功能真正运行。
