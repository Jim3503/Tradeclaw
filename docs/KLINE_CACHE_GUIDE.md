# K线缓存和分析历史系统使用指南

## 🎯 功能概述

系统现在包含三大核心功能：

### 1. **K线数据缓存**
- ✅ 自动缓存每次获取的K线数据
- ✅ 增量更新：只拉取最新数据
- ✅ 跨会话持久化保存
- ✅ 大幅提升数据获取速度

### 2. **分析历史记录**
- ✅ 保存每次完整的市场分析
- ✅ 记录持仓、技术面、建议
- ✅ 自动添加标签和分类
- ✅ 支持多维度检索

### 3. **历史交易复盘**
- ✅ 自动统计胜率、盈亏比
- ✅ 总结成功/失败经验
- ✅ 保存到记忆系统供后续学习

---

## 📦 K线缓存使用

### 自动启用（推荐）
```python
from tradeclaw.tools.fetch_data import get_stock_data

# 自动使用缓存
data = get_stock_data('600150', days=30)

# 禁用缓存（强制重新获取）
data = get_stock_data('600150', days=30, use_cache=False)
```

### 缓存文件位置
```
memory/kline_cache/
├── 600150.json          # 个股K线缓存
├── 513310.json          # ETF K线缓存
└── index.json           # 缓存索引
```

### 查看缓存统计
```python
from tradeclaw.data.kline_cache import get_kline_cache

cache = get_kline_cache()
stats = cache.get_cache_stats()

print(f"缓存股票数: {stats['total_codes']}")
print(f"总K线数: {stats['total_klines']}")
print(f"最后更新: {stats['last_update']}")
```

---

## 📊 分析历史使用

### 保存分析记录
自动在生成报告时保存，无需手动操作。

### 检索历史记录

#### 1. 按市场阶段检索
```python
from tradeclaw.memory.analysis_history import get_analysis_history

history = get_analysis_history()

# 查找所有"震荡"时期的记录
results = history.search_by_market_phase("震荡", limit=5)

for r in results:
    print(f"日期: {r['date']}")
    print(f"阶段: {r['market_phase']}")
```

#### 2. 按热点板块检索
```python
# 查找所有涉及"半导体"的分析
results = history.search_by_hot_sector("半导体", limit=5)

for r in results:
    print(f"日期: {r['date']}")
    print(f"板块: {r['hot_sector']}")
```

#### 3. 查找相似市场环境
```python
# 根据当前市场数据，查找历史相似情况
current_market = {
    '上证指数': {'close': 3200, 'change': 0.5},
    '深证成指': {'close': 11500, 'change': 1.2}
}

similar = history.get_similar_market(current_market, limit=3)

for s in similar:
    print(f"日期: {s['date']}")
    print(f"相似度: {s['similarity']:.2%}")
    print(f"当时建议: {s['recommendations']}")
```

### 历史记录文件
```
memory/analysis_history/
├── analysis_2026-05-07.json
├── analysis_2026-05-06.json
└── index.json
```

---

## 📈 历史交易复盘

### 自动生成
每次生成报告时，系统会自动：
1. 统计历史交易胜率
2. 计算平均盈利/亏损
3. 总结经验教训
4. 保存到记忆系统

### 报告中的复盘内容
```
### 历史交易复盘

**📊 交易统计**
- 总交易次数：15 笔
- 盈利次数：9 笔
- 亏损次数：6 笔
- 胜率：60.0%
- 平均盈利：+8.5%
- 平均亏损：-3.2%
- 盈亏比：2.66

**💡 交易总结**
当前交易系统表现优秀，胜率达到60.0%，建议保持当前策略...

**📋 交易明细**
**中国船舶(600150)**
- 买入：32.50元（2026-03-12） → 卖出：38.20元（2026-03-17）
- 盈利：+17.54%
- 复盘：波段操作✅成功...
```

---

## 🔧 高级用法

### 清除缓存
```python
from tradeclaw.data.kline_cache import get_kline_cache
import shutil

cache = get_kline_cache()
# 备份当前缓存
# shutil.copytree(cache.cache_dir, "backup_kline_cache")

# 清除所有缓存
import os
for file in cache.cache_dir.glob("*.json"):
    if file.name != "index.json":
        file.unlink()
print("缓存已清除")
```

### 批量预加载缓存
```python
from tradeclaw.tools.fetch_data import get_stock_data
from tradeclaw.tools.fetch_data import load_holdings

holdings = load_holdings()
codes = [h['code'] for h in holdings['current_holdings']]

print("开始预加载K线缓存...")
for code in codes:
    try:
        data = get_stock_data(code, days=60)
        print(f"✅ {code} 缓存完成: {len(data['indices']['kline'])} 条")
    except Exception as e:
        print(f"❌ {code} 缓存失败: {e}")
```

---

## 📝 数据结构说明

### K线缓存数据格式
```json
{
  "code": "600150",
  "kline": [
    ["2026-05-01", "600150", 40.0, 41.0, 39.5, 40.5, 100000, 4050000],
    ["2026-05-02", "600150", 40.5, 41.5, 40.0, 41.0, 120000, 4920000]
  ],
  "data_source": "akshare_primary",
  "last_update": "2026-05-07 22:18:43",
  "kline_count": 2
}
```

### 分析历史数据格式
```json
{
  "date": "2026-05-07",
  "timestamp": "2026-05-07 22:18:43",
  "market_data": {
    "上证指数": {"close": 3200, "change": 0.5}
  },
  "holdings_analysis": {
    "600150": {"change_pct": 2.5, "trend": "up"}
  },
  "technical_signals": {
    "overall_trend": "up",
    "market_strength": "weak"
  },
  "hot_sectors": ["半导体", "AI"],
  "recommendations": "持有待涨...",
  "tags": ["上涨", "科技"],
  "market_phase": "温和上涨",
  "performance_summary": {
    "profitable_count": 5,
    "loss_count": 2,
    "win_rate": 0.714,
    "avg_profit": 3.2
  }
}
```

---

## ⚡ 性能优化建议

1. **首次运行**: 首次获取数据会较慢，后续会使用缓存，速度大幅提升
2. **定期清理**: 建议每月清理一次过期缓存（保留最近3个月）
3. **预加载**: 可以在市场开盘前批量预加载常看股票的数据

---

## 🐛 常见问题

### Q: 为什么第二次获取还是从API？
A: 可能是缓存文件被删除或损坏。检查 `memory/kline_cache/` 目录。

### Q: 如何强制刷新某个股票的缓存？
A:
```python
from tradeclaw.data.kline_cache import get_kline_cache
cache = get_kline_cache()
cache_file = cache.get_cache_file("600150")
cache_file.unlink()  # 删除缓存
```

### Q: 历史记录检索速度慢？
A: 索引文件会自动优化。如果记录超过100条，建议归档旧记录。

---

## 🎉 总结

现在您的系统具备：

1. ✅ **智能K线缓存** - 速度快、省流量
2. ✅ **完整分析记录** - 历史可追溯
3. ✅ **智能检索** - 相似情况快速查找
4. ✅ **交易复盘** - 从历史中学习

祝投资顺利！📈
