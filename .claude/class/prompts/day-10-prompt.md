# Day 10 - 功能开发提示词

## 操作流程

```
① 确认自己在个人分支上（git branch）
② 复制下面提示词发给 Claude
③ Claude 生成后，导入种子：
   git checkout origin/day-10 -- core/xml_processor.py
④ 运行 python app.py，测试 XXE 外部实体注入漏洞
⑤ 修复：修复代码写入 fix/xml_processor_fix.py
⑥ 提交：git add -A && git commit -m "day-10: XML导入 + XXE修复"
```

## 提示词（复制以下内容发给 Claude）

> 我当前在 AI+安全实训的个人分支上，项目已有登录、注册、上传、个人中心、页面加载、密码修改、URL抓取、Ping功能。
> 请帮我完成以下功能：
>
> **Day 10 - XML 数据导入功能**
>
> 1. 生成一个 XML 导入页面（templates/xml_import.html），包含 XML 文本编辑框和"导入"按钮
> 2. 在 app.py 中添加 XML 导入路由（/xml-import），POST 方式提交 XML 数据
> 3. 解析成功后显示导入的用户数量和用户详情
> 4. 在导航栏添加"XML导入"链接（登录后显示）
> 5. 风格统一
>
> 生成完成后告诉我，我会导入 XML 处理核心模块来让功能真正运行。
