"""
A股大盘指数数据获取工具
一次性获取上证指数、深证成指、创业板指的数据
"""
from crewai.tools import tool
from tradeclaw.tools.fetch_data import get_stock_data
import json


def _get_market_indices_impl() -> str:
    """
    内部实现函数：获取三大指数数据
    """
    # 获取三大指数的数据
    indices = {
        "上证指数": get_stock_data("sh.000001", days=30),
        "深证成指": get_stock_data("sz.399001", days=30),
        "创业板指": get_stock_data("sz.399006", days=30)
    }

    return json.dumps(indices, ensure_ascii=False, indent=2)


# 创建CrewAI工具
get_market_indices_data = tool("获取A股大盘指数数据")(_get_market_indices_impl)
