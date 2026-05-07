"""
A股市场热点数据获取工具
使用 litellm 兼容的格式
"""
from crewai.tools import tool
from tradeclaw.data.fetch_data import get_market_data
import json




@tool("获取A股市场热点数据")
def get_hot_news_data() -> str:
    """
    获取A股市场热点数据，包括热点板块、大盘指数、市场涨跌统计。

    不需要任何参数，直接调用即可获取当日市场数据。

    返回内容：
    1. 热点板块TOP15（板块名称、涨跌幅）
    2. 大盘指数（上证指数、深证成指、创业板指的当前价和涨跌幅）
    3. 市场涨跌统计（上涨、下跌、平盘家数）

    本工具无参数，直接调用即可。
    """
    data = get_market_data()
    return data