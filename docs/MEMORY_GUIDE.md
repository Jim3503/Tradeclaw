# TradeClaw Memory System - 使用指南

## ✅ 系统状态

Memory 系统已完善并测试通过！

**实现内容**：
- ✅ `core.py` - 三层记忆架构核心实现 (989行)
- ✅ `integration.py` - CrewAI Agent 集成 (488行)
- ✅ `init_memory.py` - 初始化脚本
- ✅ `test_memory.py` - 测试脚本
- ✅ 所有测试通过

## 📚 系统架构

### 三层记忆系统

1. **Policy Memory (策略记忆)**
   - 长期交易规则和原则
   - 跨会话保持稳定
   - 适合 prompt caching

2. **Episodic Memory (情景记忆)**
   - 历史交易情况和经验
   - BM25 + Embeddings 混合检索
   - 支持丰富的元数据过滤

3. **Reflection Memory (反思记忆)**
   - 高有效性验证模式 (effectiveness >= 0.7)
   - 自动从情景记忆提升
   - 跨会话学习的精华

## 🚀 快速开始

### 1. 初始化系统

```bash
# 设置 Python 路径
export PYTHONPATH=/home/ming/ai-projects/daily-report/tradeclaw/src:$PYTHONPATH

# 初始化 memory
python3 init_memory.py
```

输出：
```
✓ Added 8 default policies
✓ Added 3 sample memories

✅ Memory system initialized successfully!
   Policies: 8
   Episodic memories: 3
   Reflection patterns: 0
   Total: 11

Memory data stored in: /home/ming/ai-projects/daily-report/tradeclaw/memory
```

### 2. 运行测试

```bash
python3 test_memory.py
```

所有测试应该通过：
- ✅ Test 1: Basic Memory Operations
- ✅ Test 2: Memory Persistence
- ✅ Test 3: Scope Filtering

## 💻 基本用法

### 创建 Memory Store

```python
from tradeclaw.memory import (
    FinancialMemoryStore,
    MemoryScope,
    AgentRole,
    MemoryLevel,
    MarketRegime,
    create_memory_store
)

# 方式 1: 从零创建
memory = create_memory_store()

# 方式 2: 从目录加载
memory = FinancialMemoryStore(
    policy_file="memory/policies.json",
    episodic_file="memory/episodes.json",
    reflection_file="memory/reflections.pkl"
)
```

### 添加策略

```python
memory.policy.add_policy("永远不要在单笔交易中冒险超过2%的资金")
memory.policy.add_policy("技术指标作为确认工具，不是唯一信号")
```

### 存储交易经验

```python
# 定义 scope
scope = MemoryScope()
scope.sectors.add("Technology")
scope.market_regimes.add(MarketRegime.BULL_MARKET)
scope.time_horizons.add(TimeHorizon.SWING_TRADING)

# 添加经验
entry_id = memory.add_situation(
    situation="上证指数突破3300点，MACD金叉，成交量放大",
    recommendation="建议加仓至80%，目标位3400点",
    rationale="技术指标共振向上，突破有效，量价配合良好",
    confidence=MemoryLevel.HIGH,
    scope=scope,
    source_agent=AgentRole.TECHNICAL_ANALYST,
    tags=["技术分析", "突破", "MACD"]
)
```

### 检索相关记忆

```python
# 为特定 Agent 检索
results = memory.retrieve_for_agent(
    agent_role=AgentRole.TECHNICAL_ANALYST,
    query="指数突破",
    top_k=3,
    min_score=0.3
)

# 查看结果
for result in results:
    entry = result['entry']
    score = result['score']
    print(f"Score: {score:.2f}")
    print(f"Situation: {entry.situation}")
    print(f"Recommendation: {entry.recommendation}")
```

### 生成 Prompt 上下文

```python
# 自动生成优化的 prompt 上下文
context = memory.to_prompt_context(
    agent_role=AgentRole.TECHNICAL_ANALYST,
    query="指数突破技术位",
    scope=scope,
    top_k=3
)

# context 包含：
# 1. Trading Policies and Principles (稳定前缀)
# 2. Validated Trading Patterns (反思记忆)
# 3. Relevant Past Experiences (情景记忆)
```

### 保存 Memory

```python
from pathlib import Path

memory.save(Path("memory"))
```

## 🎯 高级功能

### Scope 过滤

```python
# 创建精确的 scope
scope = MemoryScope()
scope.agent_roles.add(AgentRole.TECHNICAL_ANALYST)
scope.sectors.add("Technology")
scope.market_regimes.add(MarketRegime.BULL_MARKET)
scope.time_horizons.add(TimeHorizon.SWING_TRADING)

# 使用 scope 过滤检索
results = memory.episodic.retrieve(
    query="stocks",
    scope=scope,
    top_k=5
)
```

### 效果跟踪

```python
# 添加结果反馈
for entry in memory.episodic.entries:
    if entry.id == entry_id:
        entry.outcome = "指数上涨至3380点，盈利+4.5%"
        entry.effectiveness = 0.85
        entry.verified = True
        break

# 如果 effectiveness >= 0.7，会自动提升到反思记忆
memory.reflection.add_pattern(entry)
```

### 混合检索

```python
# BM25 + Embeddings 混合检索
results = memory.episodic.retrieve(
    query="指数突破",
    use_hybrid=True,    # 启用混合检索
    alpha=0.5,         # 0.5=平衡, 0.0=BM25, 1.0=Embeddings
    top_k=5
)
```

## 📊 Memory 统计

```python
stats = memory.get_stats()
print(f"Policies: {stats['policy_count']}")
print(f"Episodic memories: {stats['episodic_count']}")
print(f"Reflection patterns: {stats['reflection_count']}")
print(f"Total: {stats['total_memories']}")
```

## 🔧 与 CrewAI 集成

### Memory-Enhanced Agent

```python
from tradeclaw.memory.integration import (
    MemoryEnhancedTechnicalAgent,
    MemoryEnhancedNarrativeAgent,
    MemoryEnhancedPortfolioManager
)

# 创建技术分析 Agent
technical_agent = MemoryEnhancedTechnicalAgent(memory_dir=Path("memory"))

# 使用 memory 增强的分析
analysis = technical_agent.analyze_with_memory(
    stock_data={'symbol': 'AAPL', 'price': 175.50},
    market_context="Tech stocks rallying"
)

# 存储分析结果
entry_id = technical_agent.store_analysis_result(
    situation="AAPL breaking above MA50",
    recommendation="Buy with stop loss at $172",
    technical_indicators=["MA50", "MACD", "RSI"]
)
```

### 在 CrewAI Task 中使用

```python
from crewai import Agent, Task

# 在 Agent 的 tools 中添加 memory 工具
@agent
def technical_agent(self) -> Agent:
    return Agent(
        role="技术分析专家",
        tools=[
            get_market_indices_data,
            # Memory tools will be automatically integrated
        ],
        backstory="你是一位经验丰富的技术分析专家...",
        verbose=True
    )
```

## 📁 文件结构

```
tradeclaw/
├── memory/                          # Memory 数据目录
│   ├── policies.json               # 策略记忆
│   ├── episodes.json               # 情景记忆
│   └── reflections.pkl             # 反思记忆
│
├── src/tradeclaw/
│   └── memory/                     # Memory 系统核心
│       ├── core.py                 # ✅ 核心实现 (989行)
│       ├── integration.py          # ✅ Agent 集成 (488行)
│       └── __init__.py             # ✅ 导出接口
│
├── init_memory.py                  # ✅ 初始化脚本
├── test_memory.py                  # ✅ 测试脚本
└── MEMORY_GUIDE.md                 # ✅ 本文档
```

## ⚙️ 配置选项

### Embedding 模型

```python
# 默认使用 all-MiniLM-L6-v2 (快速，质量好)
memory = EpisodicFinancialMemory(
    enable_embeddings=True,
    embedding_model="all-MiniLM-L6-v2"
)

# 可选模型：
# - all-mpnet-base-v2: 更高质量，较慢
# - paraphrase-multilingual-MiniLM-L12: 支持中文
```

### 有效性阈值

```python
# 默认只有 effectiveness >= 0.7 才会进入反思记忆
memory.reflection._effectiveness_threshold = 0.7
```

## 🔍 故障排查

### 问题：导入失败

```bash
# 确保 PYTHONPATH 设置正确
export PYTHONPATH=/home/ming/ai-projects/daily-report/tradeclaw/src:$PYTHONPATH
```

### 问题：BM25 不可用

```bash
pip install rank-bm25
```

### 问题：Embeddings 不可用

```bash
pip install sentence-transformers

# 或禁用 embeddings
memory = EpisodicFinancialMemory(enable_embeddings=False)
```

## 📚 参考资源

- **原始设计**: `reference_tradeclaw/MEMORY_README.md`
- **完整实现**: `src/tradeclaw/memory/core.py`
- **Agent 集成**: `src/tradeclaw/memory/integration.py`
- **测试脚本**: `test_memory.py`

## 🎓 最佳实践

1. **编写有效的记忆**：具体且可操作
2. **使用 scope 过滤**：精确匹配场景
3. **跟踪结果**：更新 effectiveness
4. **定期保存**：确保数据持久化
5. **监控统计**：了解 memory 使用情况

---

**版本**: 1.0.0
**最后更新**: 2026-04-17
**状态**: ✅ 生产就绪
