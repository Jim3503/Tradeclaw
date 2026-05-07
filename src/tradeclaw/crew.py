from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pathlib import Path

# 导入新的 Tool（使用 @tool 装饰器）
# 使用 AkShare 版本，更稳定
from tradeclaw.tools.hot_news_tool_akshare import get_hot_news_data_akshare as get_hot_news_data
from tradeclaw.tools.stock_price_tool import get_stock_price_data
from tradeclaw.tools.market_indices_tool_v2 import get_market_indices_data
from tradeclaw.data.fetch_data import get_hot_sectors, get_market_summary
from tradeclaw.memory.core import FinancialMemoryStore, AgentRole, MemoryScope

# 配置 DeepSeek LLM
import os
from dotenv import load_dotenv
load_dotenv()

# 从环境变量读取API密钥
deepseek_key = os.getenv("DEEPSEEK_API_KEY")
if deepseek_key:
    llm = LLM(
        model="deepseek/deepseek-chat",
        api_key=deepseek_key,
        base_url="https://api.deepseek.com/v1"
    )
else:
    # 如果没有配置DeepSeek，尝试使用OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        llm = LLM(
            model="chatgpt-4o-latest",
            api_key=openai_key
        )
    else:
        raise ValueError("请在.env文件中配置DEEPSEEK_API_KEY或OPENAI_API_KEY")

# class OpenaiPipeline():
#     def __init__(self,api_key=''):
#         self.client=OpenAI(api_key=api_key)

#     def chat(self,messages,model='chatgpt-4o-latest'):
#         response = self.client.chat.completions.create(
#                                     model=model,
#                                     messages=messages
#                                 )
#         message=response.choices[0].message
#         return message.content
    
#     def chat_stream(self,messages,model="chatgpt-4o-latest"):

#         return self.client.chat.completions.create(
#             max_completion_tokens=12000,
#             messages=messages,
#             model=model,
#             stream=True
#         )
    

@CrewBase
class Tradeclaw():
    """Tradeclaw crew - 每日A股早报系统"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @property
    def memory_store(self):
        """延迟加载记忆系统（避免与 CrewBase 的 __init__ 冲突）"""
        if not hasattr(self, '_memory_store'):
            from tradeclaw.memory.core import EpisodicFinancialMemory

            memory_dir = Path('memory')
            memory_dir.mkdir(exist_ok=True)

            # 加载 policy 和 reflection
            self._memory_store = FinancialMemoryStore(
                policy_file=memory_dir / 'policies.json',
                episodic_file=memory_dir / 'episodes.json',
                reflection_file=memory_dir / 'reflections.pkl'
            )

            # 临时禁用 embeddings 以加快速度（避免下载模型）
            # 如果需要语义搜索，可以设置为 True
            enable_embeddings = False  # 暂时禁用，仅使用 BM25
            self._memory_store.episodic.enable_embeddings = enable_embeddings

            stats = self._memory_store.get_stats()
            mode = "语义搜索 + BM25" if enable_embeddings else "BM25"
            print(f"✅ 记忆系统已加载 ({mode}): {stats['total_memories']} 条记忆")
        return self._memory_store

    # ========================================
    # Agent 定义
    # ========================================

    @agent
    def data_fetcher_agent(self) -> Agent:
        """数据获取专家 - 记忆增强版"""
        # 使用记忆系统增强 backstory
        memory_context = self.memory_store.to_prompt_context(
            agent_role=AgentRole.NARRATIVE_ANALYST,  # 数据获取也可以参考叙事分析的记忆
            query="数据获取 市场环境 K线数据 热点板块",
            scope=MemoryScope(),
            top_k=3
        )

        return Agent(
            role="A股市场数据获取专家（记忆增强）",
            goal="获取当日真实的市场数据，结合历史经验优化数据获取策略",
            backstory=f"""你是一位专业的数据获取专家，负责收集A股市场的真实数据。

## 🧠 历史数据获取经验参考
{memory_context}

**重要提示**：
1. 参考以上历史经验，但今日数据必须通过工具实时获取
2. 优先使用已经验证可靠的数据源
3. 如果某个数据源在历史中出现问题，应提前准备备用方案

你的任务：
1. 调用工具获取热点板块数据
2. 调用工具获取大盘指数数据
3. 调用工具获取持仓股票的60日K线数据
4. 将数据整理成清晰的格式供其他Agent使用

你必须：
- 使用工具获取真实数据
- 不要编造任何数据
- 返回结构化的数据摘要
- 注意数据的时间戳和一致性""",
            llm=llm,
            tools=[get_hot_news_data, get_market_indices_data, get_stock_price_data],
            verbose=True,
            max_execution_time=180,
            max_iter=15,
            allow_delegation=False
        )

    @agent
    def narrative_agent(self) -> Agent:
        """市场热点叙事分析师 - 记忆增强版"""
        # 从配置文件加载基础配置
        base_config = self.agents_config['narrative_agent'].copy()

        # 使用记忆系统增强 backstory
        memory_context = self.memory_store.to_prompt_context(
            agent_role=AgentRole.NARRATIVE_ANALYST,
            query="市场热点板块分析 政策驱动 行业趋势",
            scope=MemoryScope(),
            top_k=3
        )

        # 将记忆上下文添加到 backstory
        enhanced_backstory = f"""{base_config.get('backstory', '')}

## 🧠 历史经验参考
{memory_context}

请参考以上历史经验，但要以今日真实数据为准。"""
        base_config['backstory'] = enhanced_backstory

        return Agent(
            config=base_config,
            llm=llm,
            tools=[get_hot_news_data],
            verbose=True,
            max_execution_time=300,
            max_iter=15,
            allow_delegation=False
        )

    @agent
    def technical_agent(self) -> Agent:
        """技术分析专家 - 记忆增强版"""
        # 从配置文件加载基础配置
        base_config = self.agents_config['technical_agent'].copy()

        # 使用记忆系统增强 backstory
        memory_context = self.memory_store.to_prompt_context(
            agent_role=AgentRole.TECHNICAL_ANALYST,
            query="技术分析 均线系统 支撑位 阻力位 趋势判断",
            scope=MemoryScope(),
            top_k=3
        )

        # 将记忆上下文添加到 backstory
        enhanced_backstory = f"""{base_config.get('backstory', '')}

## 🧠 历史经验参考
{memory_context}

请参考以上历史经验，但要以今日真实数据为准。"""
        base_config['backstory'] = enhanced_backstory

        return Agent(
            config=base_config,
            llm=llm,
            tools=[get_market_indices_data],  # 保留工具，但主要依赖context
            verbose=True,
            max_execution_time=300,
            max_iter=15,
            allow_delegation=False
        )

    # @agent
    # def sentiment_agent(self) -> Agent:
    #     """市场情绪分析师"""
    #     return Agent(
    #         config=self.agents_config['sentiment_agent'],
    #         llm=llm,
    #         verbose=True
    #     )

    @agent
    def report_compiler(self) -> Agent:
        """报告整合专家"""
        return Agent(
            config=self.agents_config['report_compiler'],
            llm=llm,
            verbose=True
        )

    # ========================================
    # Task 定义
    # ========================================

    @task
    def data_fetch_task(self) -> Task:
        """数据获取任务 - 第一个执行"""

        # 加载持仓配置
        from tradeclaw.tools.fetch_data import load_holdings, get_stock_data

        holdings = load_holdings()
        current_holdings = holdings.get('current_holdings', [])
        closed_trades = holdings.get('closed_trades', [])

        # 预加载持仓股票数据（确保一定获取到真实数据）
        stock_data_summary = []

        # 获取当前持仓数据
        for h in current_holdings:
            try:
                data = get_stock_data(h['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])

                if kline:
                    latest = kline[-1]
                    prices = [float(k[5]) for k in kline]

                    # 计算盈亏
                    current_price = float(latest[5])
                    cost_price = h['cost']
                    profit_loss = ((current_price - cost_price) / cost_price * 100)
                    profit_amount = (current_price - cost_price) * h['quantity']

                    stock_data_summary.append(f"""
【{h['name']}({h['code']})】
- 持仓：{h['quantity']}股，成本{h['cost']}元
- 最新价：{current_price:.2f}元
- 盈亏：{profit_loss:+.2f}%（{profit_amount:+.2f}元）
- 60日最高：{max(prices):.2f}元
- 60日最低：{min(prices):.2f}元
- 60日涨跌：{((prices[-1] - prices[0]) / prices[0] * 100):+.2f}%
""")
            except Exception as e:
                stock_data_summary.append(f"\n【{h['name']}({h['code']})】数据获取失败: {e}")

        # 获取历史交易数据
        for t in closed_trades:
            try:
                data = get_stock_data(t['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])

                stock_data_summary.append(f"""
【{t['name']}({t['code']})- 已卖出】
- 买入：{t['buy_price']}元（{t.get('buy_date', 'N/A')}）
- 卖出：{t['sell_price']}元（{t.get('sell_date', 'N/A')}）
- 盈利：{t.get('profit', 'N/A')}
- 备注：可用于复盘买卖点时机
""")
            except Exception as e:
                stock_data_summary.append(f"\n【{t['name']}({t['code']})】数据获取失败: {e}")

        holdings_data_str = "\n".join(stock_data_summary)

        # 构建任务描述
        holdings_list = []
        for h in current_holdings:
            holdings_list.append(f"- {h['name']}({h['code']}): 持仓{h['quantity']}股，成本{h['cost']}元")

        for t in closed_trades:
            holdings_list.append(f"- {t['name']}({t['code']}): 已卖出，盈利{t.get('profit', 'N/A')}")

        holdings_str = "\n".join(holdings_list)

        return Task(
            description=f"""获取当日A股市场的真实数据：

【第一步】获取热点板块数据
调用「获取A股市场热点数据」工具，获取当日热点板块TOP10

【第二步】获取大盘指数数据
调用「获取A股大盘指数数据」工具，获取上证指数、深证成指、创业板指

【第三步】持仓股票数据（已预加载）
以下持仓股票的60日K线数据已经获取：

{holdings_data_str}

【输出格式要求】
1. 热点板块：列出TOP5板块名称和涨跌幅
2. 大盘指数：列出上证指数、深证成指、创业板指的当前点位和涨跌幅
3. 持仓股票：汇总上方预加载的持仓数据

重要：直接使用上方已获取的真实持仓数据进行分析！""",
            expected_output="包含热点板块、大盘指数和持仓股票数据的完整报告",
            agent=self.data_fetcher_agent(),
        )

    @task
    def narrative_task(self) -> Task:
        """热点叙事分析任务"""
        return Task(
            config=self.tasks_config['narrative_task'],
            context=[self.data_fetch_task()],  # 依赖数据获取任务的输出
        )

    @task
    def technical_task(self) -> Task:
        """技术分析任务"""

        # 加载持仓配置并预加载详细数据
        from tradeclaw.tools.fetch_data import load_holdings, get_stock_data

        holdings = load_holdings()
        current = holdings.get('current_holdings', [])
        closed = holdings.get('closed_trades', [])

        # 预加载所有持仓的详细K线数据
        holdings_detailed = []
        for h in current:
            try:
                data = get_stock_data(h['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])

                if kline:
                    latest = kline[-1]
                    prices = [float(k[5]) for k in kline]

                    # 计算技术指标
                    current_price = float(latest[5])
                    cost_price = h['cost']
                    profit_loss = ((current_price - cost_price) / cost_price * 100)
                    profit_amount = (current_price - cost_price) * h['quantity']

                    # 计算均线
                    if len(kline) >= 20:
                        ma5 = sum([float(k[5]) for k in kline[-5:]]) / 5
                        ma10 = sum([float(k[5]) for k in kline[-10:]]) / 10
                        ma20 = sum([float(k[5]) for k in kline[-20:]]) / 20
                    else:
                        ma5 = ma10 = ma20 = current_price

                    holdings_detailed.append(f"""
【{h['name']}({h['code']})】详细技术数据：
- 持仓情况：{h['quantity']}股，成本{h['cost']}元
- 最新价格：{current_price:.2f}元（盈亏{profit_loss:+.2f}%，{profit_amount:+.2f}元）
- 60日区间：最高{max(prices):.2f}元，最低{min(prices):.2f}元
- 均线系统：MA5={ma5:.2f}，MA10={ma10:.2f}，MA20={ma20:.2f}
- 趋势判断：{'上升' if current_price > ma5 > ma10 > ma20 else '下降' if current_price < ma5 < ma10 < ma20 else '震荡'}
- 支撑位：{min(prices[-20:]) * 0.98:.2f}元
- 阻力位：{max(prices[-20:]) * 1.02:.2f}元
""")
            except Exception as e:
                holdings_detailed.append(f"\n【{h['name']}({h['code']})】数据获取失败: {e}\n")

        # 历史交易复盘数据
        for t in closed:
            try:
                data = get_stock_data(t['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])

                holdings_detailed.append(f"""
【{t['name']}({t['code']})- 历史交易复盘】
- 买入信息：{t['buy_price']}元（{t.get('buy_date', 'N/A')}）
- 卖出信息：{t['sell_price']}元（{t.get('sell_date', 'N/A')}）
- 盈利情况：{t.get('profit', 'N/A')}
- 持仓天数：5个交易日
- 复盘：短波段操作成功，抓住了上涨机会，值得总结经验
""")
            except Exception as e:
                holdings_detailed.append(f"\n【{t['name']}({t['code']})】数据获取失败: {e}\n")

        # 构建完整的任务描述
        holdings_data_str = "\n".join(holdings_detailed)

        task_config = self.tasks_config['technical_task'].copy()
        original_desc = task_config.get('description', '')

        enhanced_description = f"""【重要】以下持仓股票的详细技术数据已经预加载，请直接使用这些数据进行分析：

{holdings_data_str}

【分析要求】
基于上述详细技术数据，对每只持仓股票进行分析：
1. 技术趋势分析（基于均线系统）
2. 支撑位/阻力位分析
3. 操作建议（持有/加仓/减仓/卖出）
4. 历史交易复盘总结

{original_desc}
"""

        task_config['description'] = enhanced_description

        return Task(
            config=task_config,
        )

    # @task
    # def sentiment_task(self) -> Task:
    #     """情绪分析任务"""
    #     return Task(
    #         config=self.tasks_config['sentiment_task'],
    #     )

    @task
    def compile_report_task(self) -> Task:
        """报告整合任务"""

        # 生成带日期的文件名，避免覆盖历史报告
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        report_filename = f'reports/daily_report_{today}.md'

        # 获取真实数据用于填充报告
        from tradeclaw.tools.fetch_data import get_stock_data, load_holdings

        # 1. 获取大盘指数真实数据
        real_indices = {}
        for code, name in [("sh.000001", "上证指数"), ("sz.399001", "深证成指"), ("sz.399006", "创业板指")]:
            data = get_stock_data(code, days=30)
            kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])
            if kline:
                latest = kline[-1]
                close = float(latest[5])
                # 计算涨跌幅：如果有前一日数据，就用前一日收盘价计算
                if len(kline) >= 2:
                    prev_close = float(kline[-2][5])
                    change = ((close - prev_close) / prev_close) * 100
                elif len(latest) > 12:
                    # 如果数据格式有第12列（涨跌幅），直接使用
                    change = float(latest[12])
                else:
                    change = 0.0
                real_indices[name] = {'close': close, 'change': change}

        # 2. 获取持仓分析数据
        holdings = load_holdings()
        current = holdings.get('current_holdings', [])
        closed = holdings.get('closed_trades', [])

        holdings_analysis = ["## 五、持仓股票分析\n"]
        holdings_analysis.append("### 当前持仓技术分析\n")

        for h in current:
            try:
                data = get_stock_data(h['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])

                if kline:
                    latest = kline[-1]
                    prices = [float(k[5]) for k in kline]
                    current_price = float(latest[5])
                    cost_price = h['cost']
                    profit_loss = ((current_price - cost_price) / cost_price * 100)
                    profit_amount = (current_price - cost_price) * h['quantity']

                    # 均线
                    if len(kline) >= 20:
                        ma5 = sum([float(k[5]) for k in kline[-5:]]) / 5
                        ma20 = sum([float(k[5]) for k in kline[-20:]]) / 20
                    else:
                        ma5 = ma20 = current_price

                    # 趋势判断和操作建议
                    if current_price > ma5:
                        trend = "上升"
                        suggestion = "持有/加仓"
                    elif current_price < ma5 * 0.95:
                        trend = "下降"
                        suggestion = "减仓/观望"
                    else:
                        trend = "震荡整理"
                        suggestion = "持有"

                    holdings_analysis.append(f"""
**{h['name']}({h['code']})**
- **持仓情况**：{h['quantity']}股，成本{h['cost']}元
- **最新价格**：{current_price:.2f}元
- **盈亏情况**：{profit_loss:+.2f}%（{profit_amount:+.2f}元）
- **技术分析**：{trend}趋势，MA5={ma5:.2f}元，支撑{min(prices[-20:]):.2f}元，阻力{max(prices[-20:]):.2f}元
- **操作建议**：{suggestion}
""")
            except Exception as e:
                holdings_analysis.append(f"\n**{h['name']}({h['code']})**\n数据获取失败: {e}\n")

        # 历史交易复盘（增强版）
        if closed:
            holdings_analysis.append("\n### 历史交易复盘\n")

            # 统计总结
            profitable_trades = [t for t in closed if '+' in str(t.get('profit', ''))]
            losing_trades = [t for t in closed if '-' in str(t.get('profit', ''))]

            win_rate = len(profitable_trades) / len(closed) if closed else 0
            avg_profit = sum([float(str(t.get('profit', '0')).replace('%', '').replace('+', '')) for t in profitable_trades]) / len(profitable_trades) if profitable_trades else 0
            avg_loss = sum([float(str(t.get('profit', '0')).replace('%', '').replace('-', '')) for t in losing_trades]) / len(losing_trades) if losing_trades else 0

            holdings_analysis.append(f"""
**📊 交易统计**
- 总交易次数：{len(closed)} 笔
- 盈利次数：{len(profitable_trades)} 笔
- 亏损次数：{len(losing_trades)} 笔
- 胜率：{win_rate:.1%}
- 平均盈利：{avg_profit:.2f}%
- 平均亏损：{avg_loss:.2f}%
- 盈亏比：{avg_profit/avg_loss if avg_loss > 0 else 0:.2f}

**💡 交易总结**
""")

            if win_rate >= 0.6:
                holdings_analysis.append(f"当前交易系统表现优秀，胜率达到{win_rate:.1%}，建议保持当前策略，严格执行交易纪律。\n\n")
            elif win_rate >= 0.4:
                holdings_analysis.append(f"当前交易系统表现平稳，胜率{win_rate:.1%}，建议总结盈利交易的经验，优化亏损交易的止损策略。\n\n")
            else:
                holdings_analysis.append(f"当前交易系统需要改进，胜率仅为{win_rate:.1%}，建议：\n")
                holdings_analysis.append("1. 减少交易频率，等待更确定的机会\n")
                holdings_analysis.append("2. 严格执行止损，避免小亏变大亏\n")
                holdings_analysis.append("3. 复盘所有亏损交易，找出共同原因\n\n")

            # 详细交易列表
            holdings_analysis.append("**📋 交易明细**\n\n")
            for t in closed:
                profit = t.get('profit', 'N/A')
                is_profit = '+' in str(profit)

                holdings_analysis.append(f"""
**{t['name']}({t['code']})**
- 买入：{t['buy_price']}元（{t.get('buy_date', 'N/A')}） → 卖出：{t['sell_price']}元（{t.get('sell_date', 'N/A')}）
- 盈利：{profit}
- 复盘：波段操作{'✅成功' if is_profit else '❌失败'}，{t.get('buy_date', '')}到{t.get('sell_date', '')}的收益为{profit}
""")

        holdings_str = "\n".join(holdings_analysis)

        # 增强任务描述
        task_config = self.tasks_config['compile_report_task'].copy()
        original_description = task_config.get('description', '')

        data_note = f"""
【重要】在整合报告时，请包含以下内容：

{holdings_str}

【大盘指数真实数据】
上证指数：{real_indices['上证指数']['close']:.0f}点（{real_indices['上证指数']['change']:+.2f}%）
深证成指：{real_indices['深证成指']['close']:.0f}点（{real_indices['深证成指']['change']:+.2f}%）
创业板指：{real_indices['创业板指']['close']:.0f}点（{real_indices['创业板指']['change']:+.2f}%）

{original_description}
"""

        task_config['description'] = data_note

        return Task(
            config=task_config,
            output_file=report_filename  # 使用带日期的文件名
        )

    # ========================================
    # Crew 定义
    # ========================================
    @crew
    def crew(self) -> Crew:
        """Creates the Tradeclaw crew - 顺序执行四大任务"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
