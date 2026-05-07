"""
A股大盘指数数据获取工具（返回文本格式）
"""
from crewai.tools import tool
from tradeclaw.tools.fetch_data import get_stock_data


def _get_indices_data_raw() -> str:
    """
    获取三大指数的摘要数据（文本格式）

    Returns:
        str: 包含三大指数数据的文本摘要
    """
    lines = ["【A股大盘指数数据】", "="*50]

    for code, name in [("sh.000001", "上证指数"), ("sz.399001", "深证成指"), ("sz.399006", "创业板指")]:
        data = get_stock_data(code, days=30)
        kline = data['indices']['kline']
        if kline:
            latest = kline[-1]
            close = float(latest[5])
            change = float(latest[12])

            # 计算近期高低点
            recent_prices = [float(k[5]) for k in kline[-10:]]
            high_10d = max(recent_prices)
            low_10d = min(recent_prices)

            lines.append(f"\n{name}（{code}）")
            lines.append(f"  最新日期: {latest[0]}")
            lines.append(f"  当前点位: {close:.0f} 点")
            lines.append(f"  涨跌幅: {change:+.2f}%")
            lines.append(f"  近10日高点: {high_10d:.0f} 点")
            lines.append(f"  近10日低点: {low_10d:.0f} 点")
            lines.append(f"  支撑位参考: {low_10d:.0f}-{close*0.97:.0f} 点")
            lines.append(f"  阻力位参考: {close*1.03:.0f}-{high_10d:.0f} 点")

    return "\n".join(lines)


# 创建CrewAI工具
get_market_indices_data = tool("获取A股大盘指数数据")(_get_indices_data_raw)
