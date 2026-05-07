"""
A股市场热点数据获取工具 - 使用 AkShare（稳定版）
替换不稳定的东方财富API
"""
from crewai.tools import tool
from tradeclaw.data.akshare_data import get_hot_sectors_akshare, get_market_indices_akshare
import json


@tool("获取A股市场热点数据-AkShare版")
def get_hot_news_data_akshare() -> str:
    """
    获取A股市场热点数据（使用AkShare，更稳定）

    不需要任何参数，直接调用即可获取当日市场数据。

    返回内容：
    1. 热点板块TOP10（板块名称、涨跌幅）
    2. 大盘指数（上证指数、深证成指、创业板指的当前价和涨跌幅）
    3. 市场概况

    本工具无参数，直接调用即可。
    """
    result = []

    try:
        # 1. 获取热点板块
        sectors = get_hot_sectors_akshare(limit=10)

        if sectors:
            result.append("【当日热点板块TOP10】")
            for i, sector in enumerate(sectors, 1):
                result.append(f"{i}. {sector['name']} ({sector['change_pct']:+.2f}%)")
        else:
            result.append("【当日热点板块】暂无数据")

        result.append("")

        # 2. 获取大盘指数
        indices = get_market_indices_akshare()

        if indices:
            result.append("【大盘指数】")
            for name, data in indices.items():
                result.append(f"{name}: {data['current']:.0f}点 ({data['change_pct']:+.2f}%)")
        else:
            result.append("【大盘指数】暂无数据")

        result.append("")
        result.append("【数据来源】AkShare")

        return "\n".join(result)

    except Exception as e:
        return f"获取市场数据失败: {str(e)}"
