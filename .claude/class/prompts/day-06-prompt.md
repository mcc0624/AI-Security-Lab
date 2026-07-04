# Day 6 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-06 -- core/page_loader.py
④ 运行 python app.py，测试 LFI 文件包含漏洞
⑤ 修复：修复代码写入 fix/page_loader_fix.py
⑥ 提交：git add -A && git commit -m "day-06: 动态页面加载 + LFI修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、上传、个人中心功能。
> 请帮我完成以下功能：
>
> **Day 6 - 动态页面加载功能**
>
> 1. 在 app.py 中添加动态页面加载路由（/page），通过 URL 参数 name 加载不同页面
> 2. 在首页添加一个"帮助中心"入口链接
> 3. 页面加载成功后，在首页下方显示加载的页面内容
> 4. 页面加载失败时显示"页面不存在"提示
> 5. 风格统一
>
> 生成完成后告诉我，我会导入页面加载核心模块来让功能真正运行。
