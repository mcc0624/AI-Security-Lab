# Day 7 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-07 -- core/password_manager.py
④ 运行 python app.py，测试 CSRF 跨站请求伪造漏洞
⑤ 修复：修复代码写入 fix/password_manager_fix.py
⑥ 提交：git add -A && git commit -m "day-07: 密码修改 + CSRF修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、上传、个人中心、页面加载功能。
> 请帮我完成以下功能：
>
> **Day 7 - 密码修改功能**
>
> 1. 在 app.py 中添加密码修改路由（/change-password），POST 方式提交新密码
> 2. 在个人中心页面添加密码修改表单（新密码输入框 + 确认按钮）
> 3. 修改成功后跳回个人中心并提示"密码修改成功"
> 4. 风格统一
>
> 生成完成后告诉我，我会导入密码管理核心模块来让功能真正运行。
