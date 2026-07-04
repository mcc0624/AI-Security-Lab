# Day 4 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-04 -- core/file_handler.py
④ 运行 python app.py，测试任意文件上传漏洞
⑤ 修复：修复代码写入 fix/file_handler_fix.py
⑥ 提交：git add -A && git commit -m "day-04: 文件上传 + 任意上传修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、搜索功能。
> 请帮我完成以下功能：
>
> **Day 4 - 用户头像上传功能**
>
> 1. 生成一个上传页面（templates/upload.html），包含文件选择按钮和上传按钮
> 2. 在 app.py 中添加上传路由（/upload），接收文件并保存到 static/uploads/
> 3. 上传成功后显示图片预览和文件访问地址
> 4. 在导航栏添加"上传头像"链接（登录后显示）
> 5. 在首页添加上传头像的快捷入口
> 6. 上传失败时显示错误提示
> 7. 页面风格统一
>
> 生成完成后告诉我，我会导入文件处理核心模块来让功能真正运行。
