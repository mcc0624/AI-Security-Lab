# Day 3 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-03 -- core/database.py
④ 运行 python app.py，搜索功能测试 SQL 注入
⑤ 修复：修复代码写入 fix/database_fix.py
⑥ 提交：git add -A && git commit -m "day-03: 注册搜索 + SQL注入修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录功能。
> 请帮我完成以下功能：
>
> **Day 3 - 用户注册与搜索功能**
>
> 1. 生成一个注册页面（templates/register.html），包含用户名、密码、邮箱、手机号输入框
> 2. 在 app.py 中添加注册路由（/register），将数据提交到后端
> 3. 在 app.py 中添加搜索用户路由（/search），通过 URL 参数 keyword 搜索
> 4. 在首页（templates/index.html）添加搜索输入框，搜索结果显示在下方
> 5. 在导航栏添加"注册"链接（未登录时显示）
> 6. 注册成功后跳转到登录页并提示"注册成功，请登录"
> 7. 页面风格统一，与登录页保持一致
>
> 生成完成后告诉我，我会导入数据库核心模块来让功能真正运行。
