from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from fetch_data import get_stock_data
import json


class MarketDataInput(BaseModel):
    """Input schema for MyCustomTool."""
    argument: str = Field(..., description="A股股票代码，例如 002463、601899。用于查询该股票的实时价格和行情数据。")
    pass

class MarketDataTool(BaseTool):
    name: str = "获取A股个股价格与行情数据"
    description: str = (
        "用于获取指定A股股票的实时价格与基础行情数据，适用于交易复盘、技术分析、买卖点分析等场景。"
        "返回内容应尽量包括："
        "1. 股票名称与代码；"
        "2. 当前价、昨收价、开盘价；"
        "3. 最高价、最低价；"
        "4. 成交量、成交额、换手率；"
        "5. 如有需要，可补充最近60日K线数据，用于计算MA5、MA10、MA20、MA60、近期高低点和量价关系。"
        "本工具只负责返回个股行情与价格事实数据，不负责直接给出买卖建议。"
    )
    args_schema: Type[BaseModel] = MarketDataInput

    def _run(self, stock_code: str) -> str:
        # Implementation goes here
        # 这里调用你的数据获取函数
        # 返回实际的市场数据
        data = get_stock_data(stock_code, days=30)
        return json.dumps(data, ensure_ascii=False)