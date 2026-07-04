# Day 2 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-02 -- core/auth.py
④ 运行 python app.py，观察漏洞
⑤ 修复：修复代码写入 fix/auth_fix.py
⑥ 提交：git add -A && git commit -m "day-02: 登录功能 + 密码泄露修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目基础框架已就绪（Flask + base 模板）。
> 请帮我完成以下功能：
>
> **Day 2 - 用户登录功能**
>
> 1. 生成一个登录页面（templates/login.html），包含用户名和密码输入框、登录按钮
> 2. 在 app.py 中添加登录路由（/login），用 POST 方法接收表单数据
> 3. 登录成功后跳转到首页并显示 "欢迎回来，用户名"
> 4. 登录失败时在登录页显示错误提示
> 5. 添加登出路由（/logout），清除 session 后跳转到首页
> 6. 页面风格简洁美观，使用卡片式布局
> 7. 更新 templates/base.html 的导航栏，登录后显示"欢迎"和"退出"链接
> 8. 更新 templates/index.html，登录后显示用户信息和操作入口
>
> 生成完成后告诉我，我会导入核心认证模块来让登录功能真正运行。
