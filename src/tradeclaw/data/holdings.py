"""
持仓股票数据
根据你的实盘记录
"""

# 当前持仓
CURRENT_HOLDINGS = [
    {
        "code": "601899",
        "name": "紫金矿业",
        "position": "100股",
        "cost": 34.89,
        "current_price": 34.90,  # 需要实时获取
        "PnL": "+0.03%"
    },
    {
        "code": "513310",
        "name": "中韩半导体ETF",
        "position": "6100份",
        "cost": 1.20,  # 假设成本
        "current_price": 1.28,  # 假设现价
        "PnL": "+6.32%"
    }
]

# 已卖出（用于复盘）
CLOSED_TRADES = [
    {
        "code": "002463",
        "name": "沪电股份",
        "buy_date": "2026-03-12",
        "buy_price": 76.88,
        "sell_date": "2026-03-17",
        "sell_price": 89.57,
        "PnL": "+16.51%",
        "profit": 1269
    }
]

def get_holdings_summary():
    """获取持仓摘要"""
    summary = "【当前持仓】\n"
    for h in CURRENT_HOLDINGS:
        summary += f"- {h['name']}({h['code']}): {h['position']}, 成本 {h['cost']}元, 现价 {h['current_price']}元, 盈亏 {h['PnL']}\n"
    
    summary += "\n【历史交易】\n"
    for t in CLOSED_TRADES:
        summary += f"- {t['name']}({t['code']}): {t['buy_date']}买入{t['buy_price']}元 → {t['sell_date']}卖出{t['sell_price']}元, 盈利{t['PnL']}\n"
    
    return summary
