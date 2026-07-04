# Day 5 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-05 -- core/user_service.py
④ 运行 python app.py，测试越权和支付漏洞
⑤ 修复：修复代码写入 fix/user_service_fix.py
⑥ 提交：git add -A && git commit -m "day-05: 个人中心充值 + 越权支付修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、搜索、上传功能。
> 请帮我完成以下功能：
>
> **Day 5 - 个人中心与充值功能**
>
> 1. 生成一个个人中心页面（templates/profile.html），显示用户信息（用户名、邮箱、手机、角色、余额）
> 2. 在 app.py 中添加查看个人资料路由（/profile），通过 URL 参数 user_id 查询
> 3. 在 app.py 中添加修改资料路由（/update-profile），POST 方式提交
> 4. 在 app.py 中添加充值路由（/recharge），POST 方式提交金额
> 5. 在导航栏添加"个人中心"链接（登录后显示）
> 6. 修改资料和充值成功后刷新个人中心页面
> 7. 页面风格统一
>
> 生成完成后告诉我，我会导入用户服务核心模块来让功能真正运行。
