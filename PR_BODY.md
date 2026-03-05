## 更新内容

### 新增模块
- **LLM 客户端** (`src/llm/__init__.py`)
  - 统一的大语言模型调用接口
  - 支持多种提供商: OpenAI、Moonshot(Kimi)、DeepSeek、通义千问
  - 支持流式对话和文本嵌入
  - 可从环境变量自动配置

- **工具集** (`src/tools/tools.py`)
  - `TimeTool`: 获取当前时间
  - `CalculatorTool`: 数学计算
  - `MemoryStoreTool`: 存储长期记忆
  - `MemoryRetrieveTool`: 检索长期记忆
  - `WeatherTool`: 天气查询(模拟)
  - `WebSearchTool`: 网页搜索(支持 Brave/Serper)
  - `TaskManagerTool`: 任务管理

### 重构节点
- `intent_analysis_node`: 使用 LLM 进行意图识别
- `store_memory_node`: 集成记忆存储工具
- `retrieve_memory_node`: 集成记忆检索工具
- `task_manager_node`: 集成任务管理工具
- `search_node`: 集成搜索工具
- `generate_response_node`: 支持工具调用的对话生成

### 依赖更新
- 添加 `openai>=1.0.0`
- 添加 `pytz>=2024.1`
- 添加 `aiohttp>=3.9.0`
