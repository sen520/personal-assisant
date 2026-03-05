# Personal Assistant

基于 LangGraph 的个人智能助理系统。

## 功能特性

- 🤖 智能对话与任务处理
- 🧠 长期记忆管理
- 📅 日程与提醒
- 🔍 信息检索与整合
- 📝 知识库管理

## 项目结构

```
personal-assistant/
├── src/
│   ├── graph/          # LangGraph 工作流定义
│   ├── nodes/          # 功能节点
│   ├── state/          # 状态管理
│   ├── tools/          # 工具集合
│   ├── utils/          # 工具函数
│   └── config/         # 配置管理
├── tests/              # 测试用例
├── memory/             # 记忆存储
├── prompts/            # 提示词模板
└── logs/               # 日志文件
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```