# TradeClaw - 智能A股分析系统

<div align="center">

  **出品方：《吉米仔策略室》公众号**

  [![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![CrewAI](https://img.shields.io/badge/CrewAI-Latest-orange.svg)](https://www.crewai.com/)

</div>

---

## 🎯 项目简介

**TradeClaw** 是一个基于 **CrewAI** 构建的智能A股分析系统，通过多Agent协作，自动生成专业、深入的每日市场早报。

### 核心特点

- 🤖 **多Agent协作** - 数据获取、叙事分析、技术分析、报告生成
- 🧠 **记忆增强** - 从历史分析中学习，持续优化投资策略
- 📊 **多源数据** - AkShare + 东方财富 + 新浪API，稳定可靠
- 💾 **智能缓存** - K线数据自动缓存，增量更新
- 📈 **交易复盘** - 自动统计胜率、盈亏比，总结经验教训

---

## 核心框架
![核心原理](v2.png)

## ✨ 主要功能

### 1. 自动生成每日早报
- 市场概览（指数涨跌、资金流向）
- 热点板块分析（叙事驱动）
- 技术面分析（均线、支撑位、阻力位）
- 持仓股票分析
- 历史交易复盘
- 综合操作建议

### 2. 智能记忆系统
- **策略记忆** - 长期有效的交易规则
- **情景记忆** - 具体市场情况的分析
- **反思记忆** - 从成功/失败中提取经验
- **语义检索** - BM25算法快速查找历史记录

### 3. K线数据缓存
- 自动缓存每次获取的数据
- 下次只获取增量数据
- 大幅提升数据获取速度
- 跨会话持久化存储

### 4. 分析历史记录
- 保存每次完整的市场分析
- 支持按市场阶段、热点板块检索
- 查找相似历史情况
- 获取历史参考建议

---

## 🚀 快速开始

### 环境要求

- Python 3.12+
- pip 或 uv

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/tradeclaw.git
cd tradeclaw

# 安装依赖
pip install -r requirements.txt

# 或使用 uv（推荐）
pip install uv
uv sync
```

### 配置

1. 复制配置模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入您的API密钥：
```bash
# 使用 DeepSeek（推荐）
DEEPSEEK_API_KEY=your_api_key_here

# 或使用 OpenAI
OPENAI_API_KEY=your_api_key_here
```

### 配置持仓

1. 复制持仓配置模板：
```bash
cp config/holdings.yaml.example config/holdings.yaml
```

2. 编辑 `config/holdings.yaml` 文件，添加您的持仓信息：

```yaml
# 当前持仓
current_holdings:
  - code: "601611"
    name: "中国核建"
    quantity: 700
    cost: 13.04

# 历史交易
closed_trades:
  - code: "002463"
    name: "沪电股份"
    buy_date: "2026-03-12"
    buy_price: 76.88
    sell_date: "2026-03-17"
    sell_price: 89.57
    quantity: 100
```

### 运行

```bash
bash run_report.sh
```

报告将保存在 `reports/daily_report_YYYY-MM-DD.md`

### 查看示例报告

项目包含一个**完整的真实报告示例**，展示了系统的实际输出质量：

```bash
cat reports/example_daily_report.md
```

**示例报告包含**：
- 📊 **市场概览** - 三大指数涨跌、核心观点
- 🔥 **热点板块叙事** - 半导体、核电、高端制造等板块深度分析
- 📈 **技术面分析** - 均线、支撑位、阻力位、趋势判断
- 💼 **持仓分析** - 7只持仓股票的详细技术分析表格
- 🎯 **操作建议** - 持股待涨、汰弱留强等策略建议
- 📚 **历史交易复盘** - 胜率64.7%、成功案例、失败教训

**示例数据说明**：
- 报告日期：2026年5月7日
- 市场数据：上证指数4180点（+0.48%）
- 持仓数量：7只（中国核建、安徽合力、海陆重工等）
- 历史交易：17笔（包含11笔成功、6笔失败）

这是系统生成的真实报告，您可以看到：
- ✅ 叙事分析如何结合市场热点
- ✅ 技术分析如何给出具体点位
- ✅ 记忆系统如何利用历史交易经验
- ✅ 多Agent如何协作生成专业报告

---

## 📁 项目结构

```
tradeclaw/
├── src/tradeclaw/          # 源代码
│   ├── config/             # Agent配置
│   ├── data/               # 数据获取模块
│   ├── tools/              # CrewAI工具
│   ├── memory/             # 记忆系统
│   ├── crew.py             # CrewAI配置
│   └── main.py             # 主入口
├── config/                 # 用户配置
│   └── holdings.yaml       # 持仓配置
├── docs/                   # 文档
├── reports/                # 生成的报告
├── memory/                 # 记忆存储
└── run_report.sh           # 运行脚本
```

---

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| AI框架 | CrewAI | 多Agent协作框架 |
| LLM | DeepSeek / OpenAI | 语言模型 |
| 数据源 | AkShare | 免费、无需注册 |
| 数据源 | 东方财富API | 免费、无需注册 |
| 数据源 | 新浪财经API | 实时行情 |
| 记忆检索 | BM25 | 语义搜索 |
| 数据格式 | Markdown / PDF | 报告格式 |

---

## 📊 数据源说明

本项目使用的所有数据源均为**免费、无需注册**的公开API：

1. **AkShare** - A股行情数据（主要）
2. **东方财富API** - 指数、ETF数据
3. **新浪财经API** - 实时行情数据

**注意**：BaoStock已停止服务，系统已完全移除对其依赖。

---

## 📖 使用指南

### 生成报告

```bash
# 标准运行
bash run_report.sh

# 或使用Python直接运行
python -m tradeclaw.main
```

### 查看缓存统计

```python
from tradeclaw.data.kline_cache import get_kline_cache

cache = get_kline_cache()
stats = cache.get_cache_stats()
print(f"缓存股票数: {stats['total_codes']}")
print(f"总K线数: {stats['total_klines']}")
```

### 检索历史分析

```python
from tradeclaw.memory.analysis_history import get_analysis_history

history = get_analysis_history()

# 查找相似市场情况
current_market = {
    '上证指数': {'close': 3200, 'change': 0.5}
}
similar = history.get_similar_market(current_market, limit=3)
```

详细文档请查看 `docs/` 目录。

---

## 📑 报告示例预览

以下是系统生成的真实报告片段（完整版见 `reports/example_daily_report.md`）：

### 市场概览
```
昨日（2026年5月6日）A股三大指数集体收涨，市场情绪偏向积极。
科技与新能源板块表现活跃，为市场提供了向上的主要动能。

| 指数名称 | 最新点数 | 涨跌幅 |
| **上证指数** | 4180点 | +0.48% |
| **深证成指** | 15642点 | +1.18% |
| **创业板指** | 3833点 | +1.45% |
```

### 持仓分析表
```
| 代码 | 名称 | 持仓成本 | 最新价 | 盈亏 | 趋势 | 操作建议 |
| 601611 | 中国核建 | 13.04元 | 13.84元 | +6.13% | 上升 | 持有/加仓 |
| 600761 | 安徽合力 | 17.48元 | 18.36元 | +5.03% | 上升 | 持有/加仓 |
| 002255 | 海陆重工 | 11.105元 | 11.37元 | +2.39% | 上升 | 持有/加仓 |
```

### 历史交易复盘
```
- 成功经验：您的历史胜率高达64.7%
- 改进方向：非主流热点或趋势不佳的个股风险较高
- 核心纪律：保持当前高胜率的交易系统
```

---

## 🎨 系统架构

系统采用多Agent协作架构：

1. **Data Fetcher Agent** - 数据获取专家（记忆增强）
2. **Narrative Agent** - 市场热点叙事分析师（记忆增强）
3. **Technical Agent** - 技术分析专家（记忆增强）
4. **Report Compiler** - 报告整合专家

完整架构图生成Prompt见：`docs/ARCHITECTURE_DIAGRAM_PROMPT.md`

---

## 📝 配置说明

### LLM选择

系统支持多种LLM：

1. **DeepSeek**（推荐）
   - 性价比高
   - 中文支持好
   - 获取地址：https://platform.deepseek.com/

2. **OpenAI**
   - GPT-4系列
   - 获取地址：https://platform.openai.com/

### 数据源优先级

1. **个股数据**：AkShare → 东方财富 → 新浪
2. **指数数据**：东方财富 → AkShare → 新浪
3. **ETF数据**：东方财富 → AkShare
4. **实时行情**：新浪API（最快）

---

## 🔒 隐私与安全

- ⚠️ **切勿提交** `.env` 文件到版本控制系统
- ⚠️ **切勿提交** `memory/` 目录到公开仓库
- ✅ `.gitignore` 已配置排除敏感文件
- ✅ 使用 `.env.example` 作为配置模板

---

## 📄 License

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

- **出品方**：《吉米仔策略室》公众号
- **邮件**：ming.ji@zju.edu.cn
---

<div align="center">
  <b>⚡ 祝投资顺利，收益长虹！</b>
</div>
