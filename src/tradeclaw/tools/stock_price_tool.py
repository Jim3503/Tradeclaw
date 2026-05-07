"""
A股个股数据获取工具
使用 @tool 装饰器，强制 Agent 调用
"""
from crewai.tools import tool
from tradeclaw.tools.fetch_data import get_stock_data
import json


@tool("获取A股个股价格与行情数据")
def get_stock_price_data(stock_code: str, days: int = 60) -> str:
    """
    【重要】这是获取A股实时行情数据的唯一工具，必须使用此工具获取真实数据。

    用途：获取指定A股股票或大盘指数的实时价格与历史行情数据

    参数：
    - stock_code: 股票或指数代码（必需）
      * 大盘指数：sh.000001（上证指数）、sz.399001（深证成指）、sz.399006（创业板指）
      * 个股：002463、601899、000001等
    - days: 获取的历史天数，默认60天

    返回内容：
    1. 证券基本信息（名称、代码）
    2. 实时行情（当前价、昨收价、开盘价、最高价、最低价、涨跌幅）
    3. 成交量数据（成交量、成交额、换手率）
    4. 历史K线数据（最近60个交易日的开高低收量）

    使用示例：
    - 上证指数：stock_code="sh.000001"
    - 深证成指：stock_code="sz.399001"
    - 创业板指：stock_code="sz.399006"
    - 紫金矿业：stock_code="601899"

    警告：不要编造数据，必须调用此工具获取真实数据！
    """
    from tradeclaw.tools.fetch_data import get_stock_data
    data = get_stock_data(stock_code, days=days)
    return json.dumps(data, ensure_ascii=False, indent=2)
