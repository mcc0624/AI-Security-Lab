# AI+安全实训 - 学生操作手册

> 四川大学网络空间安全学院 2025级 AI+安全实训项目

---

## 📋 整体流程

```
Day 1 │ 克隆项目 → 创建自己的分支 (张三-project)
Day 2 │ 复制提示词 → AI生成登录页 → 导入种子 → 发现泄露 → 修复 → 提交
Day 3 │ AI生成注册/搜索 → 导入种子 → 发现SQL注入 → 修复 → 提交
Day 4 │ AI生成上传功能 → 导入种子 → 发现文件上传漏洞 → 修复 → 提交
  ...  （以此类推到 Day 10）
      │
      └─ 最终：自己的分支上有一个完整的、修复了全部漏洞的项目成果
```

---

## 🚀 Day 1：环境搭建 + 创建个人分支

### 第一步：安装工具

```bash
python --version           # 验证 ≥ 3.10
git --version              # 验证安装成功
npm install -g @anthropic-ai/claude-code
claude --version           # 验证安装成功
pip install flask requests
```

### 第二步：克隆项目

```bash
git clone https://github.com/mcc0624/AI-Security-Lab.git
cd AI-Security-Lab
```

### 第三步：创建自己的分支（重要！）

```bash
git checkout base
git checkout -b 你的名字-project

# 例如：
git checkout -b zhangsan-project
```

> ⚠️ **这个分支将陪伴你 10 天**。每天的功能代码、修复代码都提交到这里。

### 第四步：验证环境

```bash
python app.py
# 浏览器打开 http://127.0.0.1:5000
```

---

## 📅 Day 2 ~ Day 10：每天的标准化流程

### 每天重复以下 5 步

| 步骤 | 操作 | 说明 |
|------|------|------|
| **Step 1** | 确认在自己分支上 | `git branch` 显示 `你的名字-project` |
| **Step 2** | 复制提示词给 Claude | 打开 `.claude/class/prompts/day-XX-prompt.md` |
| **Step 3** | 导入漏洞种子 | `git checkout origin/day-XX -- core/XX.py` |
| **Step 4** | 发现 + 修复漏洞 | 分析代码 → 写修复到 `fix/` |
| **Step 5** | 提交到自己的分支 | `git commit -m "day-XX: ..."` |

### 详细操作示范（以 Day 2 为例）

**Step 1：进入项目**
```bash
cd AI-Security-Lab
git branch    # 确认在 zhangsan-project 上
```

**Step 2：让 Claude 帮你生成代码**
```bash
claude /ai-security-lab
```
然后打开 `.claude/class/prompts/day-02-prompt.md`，把内容复制发给 Claude。

**Step 3：导入漏洞种子代码**
```bash
git checkout origin/day-02 -- core/auth.py
```
然后更新 `core/__init__.py` 添加导入语句。

**Step 4：运行、发现漏洞、修复**
```bash
python app.py    # 启动，观察漏洞
# 修复代码写入 fix/auth_fix.py
```

**Step 5：提交成果**
```bash
git add -A
git commit -m "day-02: 实现登录功能，修复密码泄露漏洞"
```

---

## 🔄 第二天如何继续

```bash
cd AI-Security-Lab          # 进入项目
git branch                  # 确认在 zhangsan-project 上
claude /ai-security-lab     # 开始
```

**不需要** `git checkout day-03`！你只需要导入种子：

```bash
git checkout origin/day-03 -- core/database.py
```

---

## 📁 10 天后你的项目结构

```
AI-Security-Lab/
├── core/                    ← 🔒 种子代码
│   ├── auth.py              ← Day 2 导入
│   ├── database.py          ← Day 3 导入
│   ├── file_handler.py      ← Day 4
│   ├── user_service.py      ← Day 5
│   ├── page_loader.py       ← Day 6
│   ├── password_manager.py  ← Day 7
│   ├── url_fetcher.py       ← Day 8
│   ├── command_runner.py    ← Day 9
│   └── xml_processor.py     ← Day 10
├── templates/               ← 🎨 AI 生成的页面（每人不同）
├── fix/                     ← 📝 你的修复代码
├── app.py                   ← 路由（AI生成 + 自己修改）
└── 你的名字-project         ← 🌟 你的专属分支
```

---

## ❓ 常见问题

### 不小心修改了 core/ 怎么办？
```bash
git checkout origin/day-02 -- core/auth.py    # 恢复
```

### 提交错了想回退？
```bash
git reset --soft HEAD~1
```

### 需要 git pull 吗？
**不需要。** 你每天只从 `origin/day-XX` 拉取指定种子文件，不是拉取整个分支。

### 代码冲突了怎么办？
告诉 Claude："帮我把下面的路由代码合并到我的 app.py 中"

---

## ✅ 验收标准

10 天后你的分支应该包含：

- [ ] 10 个 `core/XXX.py` 种子模块（含漏洞）
- [ ] AI 生成的页面模板（每人不同）
- [ ] `fix/` 目录下 10 个修复文件
- [ ] 可以正常运行 `python app.py`
- [ ] 所有漏洞已修复

## 📤 最终提交

```bash
git push origin 你的名字-project
```
