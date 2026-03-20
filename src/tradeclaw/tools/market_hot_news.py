from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from tradeclaw.data.fetch_data import get_market_data


class HotNewsInput(BaseModel):
    """Input schema for HotNewsInput."""
    argument: str = Field(..., description="需要查询的日期，格式如 2026-03-17。用于获取该交易日A股市场热点新闻、板块涨跌和相关催化信息。")
    pass

class HotNewsTool(BaseTool):
    name: str = "获取A股市场热点新闻与叙事数据"
    description: str = (
        "用于获取指定交易日的A股市场热点新闻、热点板块、板块涨跌幅、相关政策或事件催化、"
        "市场指数概况（如沪指、创业板）以及用于热点叙事分析的原始数据。"
        "适用于需要分析今天市场为什么涨/跌、哪些板块最强、背后有哪些消息驱动的场景。"
        "返回内容应尽量包括："
        "1. 当日热点板块TOP列表；"
        "2. 每个热点板块的涨跌幅或强弱信息；"
        "3. 相关新闻、政策、公告、产业催化；"
        "4. 沪指、创业板等主要指数的表现；"
        "5. 可用于市场叙事总结的结构化原始数据。"
        "本工具主要负责提供事实数据，不负责主观分析结论。"
    )
    args_schema: Type[BaseModel] = HotNewsInput

    def _run(self, argument: str = "") -> str:
        return get_market_data()