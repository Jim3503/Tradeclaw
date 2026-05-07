#!/usr/bin/env python
"""
TradeClaw - 每日A股早报系统
"""
import sys
import os
import warnings
import re
from datetime import datetime
from pathlib import Path

from tradeclaw.crew import Tradeclaw

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def save_to_memory(report_content: str, date: str, memory_store):
    """
    从报告中提取关键信息并保存到记忆系统

    Args:
        report_content: 生成的报告内容
        date: 报告日期
        memory_store: 记忆存储实例
    """
    from tradeclaw.memory.core import MemoryLevel, MemoryScope, AgentRole

    try:
        # 提取热点板块分析
        hot_sectors = extract_hot_sectors(report_content)
        if hot_sectors:
            memory_store.add_situation(
                situation=f"热点板块分析 - {date}",
                recommendation=f"今日热点板块: {hot_sectors}",
                rationale="基于市场数据分析的热点板块及其驱动因素",
                confidence=MemoryLevel.MEDIUM,
                scope=MemoryScope(),
                source_agent=AgentRole.NARRATIVE_ANALYST,
                tags=["热点板块", "市场分析"],
                market_conditions=f"报告日期: {date}"
            )
            print(f"   ✓ 保存热点板块分析")

        # 提取技术分析要点
        technical_points = extract_technical_analysis(report_content)
        if technical_points:
            memory_store.add_situation(
                situation=f"技术分析 - {date}",
                recommendation=f"技术分析要点: {technical_points}",
                rationale="基于真实指数数据的技术面分析",
                confidence=MemoryLevel.MEDIUM,
                scope=MemoryScope(),
                source_agent=AgentRole.TECHNICAL_ANALYST,
                tags=["技术分析", "趋势判断"],
                market_conditions=f"报告日期: {date}"
            )
            print(f"   ✓ 保存技术分析要点")

        # 保存到磁盘
        memory_store.save(Path('memory'))
        print(f"   ✓ 记忆已保存到磁盘")

    except Exception as e:
        print(f"   ⚠️ 保存记忆时出错: {e}")


def extract_hot_sectors(report_content: str) -> str:
    """从报告中提取热点板块信息"""
    # 查找热点板块相关的段落
    patterns = [
        r'热点板块[:：](.+?)(?=\n|$)',
        r'热门板块[:：](.+?)(?=\n|$)',
        r'领涨板块[:：](.+?)(?=\n|$)',
    ]

    sectors = []
    for pattern in patterns:
        matches = re.findall(pattern, report_content)
        sectors.extend(matches)

    return " | ".join(sectors[:3]) if sectors else ""


def extract_technical_analysis(report_content: str) -> str:
    """从报告中提取技术分析要点"""
    # 查找技术分析相关的关键词
    keywords = []

    if "上升" in report_content or "上涨" in report_content:
        keywords.append("上升趋势")
    if "下降" in report_content or "下跌" in report_content:
        keywords.append("下降趋势")
    if "震荡" in report_content or "整理" in report_content:
        keywords.append("震荡整理")
    if "支撑位" in report_content:
        keywords.append("关注支撑位")
    if "阻力位" in report_content:
        keywords.append("关注阻力位")

    return " | ".join(keywords) if keywords else "技术分析详见报告"

def run():
    today = datetime.now().strftime('%Y-%m-%d')
    os.makedirs('reports', exist_ok=True)
    os.makedirs('memory', exist_ok=True)

    # 初始化记忆系统
    from tradeclaw.memory.core import FinancialMemoryStore
    from tradeclaw.memory import MemoryOptimizer

    memory_dir = Path('memory')
    memory_store = FinancialMemoryStore(
        policy_file=memory_dir / 'policies.json',
        episodic_file=memory_dir / 'episodes.json',
        reflection_file=memory_dir / 'reflections.pkl'
    )

    # 创建记忆优化器
    memory_optimizer = MemoryOptimizer(memory_store)

    # 打印记忆统计信息
    stats = memory_optimizer.get_memory_stats()
    print("\n" + "="*50)
    print("📚 记忆系统已加载")
    print(f"   策略记忆: {stats['policy_count']} 条")
    print(f"   情景记忆: {stats['episodic_count']} 条")
    print(f"   反思记忆: {stats['reflection_count']} 条")
    print(f"   总计: {stats['total_memories']} 条")
    if stats.get('avg_effectiveness', 0) > 0:
        print(f"   平均效果: {stats['avg_effectiveness']:.2%}")
    print("="*50 + "\n")

    inputs = {
        'date': today,
        'current_year': str(datetime.now().year)
    }
    result = Tradeclaw().crew().kickoff(inputs=inputs)

    # 后处理：修正报告中的错误点位并添加数据说明
    from tradeclaw.tools.fetch_data import get_stock_data
    import re

    # 使用带日期的报告文件名
    report_path = f'reports/daily_report_{today}.md'
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 获取真实数据
        real_data = {}
        for code, name in [("sh.000001", "上证指数"), ("sz.399001", "深证成指"), ("sz.399006", "创业板指")]:
            data = get_stock_data(code, days=30)
            kline = data['indices']['kline']
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
                real_data[name] = {'close': close, 'change': change}

        # 定义替换规则：将常见的错误点位替换为真实点位
        replacements = []

        # 上证指数：如果出现3000-3200范围的数字，替换为真实点位
        sh_close = real_data['上证指数']['close']
        if sh_close > 3500:  # 确认真实数据是合理的
            # 匹配"上证指数...XXXX点"的模式
            content = re.sub(
                r'(上证指数[^点，。]*?)(?:约|大约|当前|收于|位于|运行在)?\s*(\d{3,4})\.?\d*\s*点',
                lambda m: f"{m.group(1)}约{int(sh_close)}点" if int(m.group(2)) < 3500 else m.group(0),
                content
            )

        # 深证成指：如果出现10000-12000范围的数字，替换为真实点位
        sz_close = real_data['深证成指']['close']
        if sz_close > 13000:
            content = re.sub(
                r'(深证成指[^点，。]*?)(?:约|大约|当前|收于|位于|运行在)?\s*(\d{4,5})\.?\d*\s*点',
                lambda m: f"{m.group(1)}约{int(sz_close)}点" if int(m.group(2)) < 12000 else m.group(0),
                content
            )

        # 创业板指：如果出现1800-2000范围的数字，替换为真实点位
        cyb_close = real_data['创业板指']['close']
        if cyb_close > 2500:
            content = re.sub(
                r'(创业板指[^点，。]*?)(?:约|大约|当前|收于|位于|运行在)?\s*(\d{3,4})\.?\d*\s*点',
                lambda m: f"{m.group(1)}约{int(cyb_close)}点" if int(m.group(2)) < 2500 else m.group(0),
                content
            )

        # 添加数据说明到报告顶部
        data_lines = [
            f"- 上证指数：{real_data['上证指数']['close']:.0f}点（{real_data['上证指数']['change']:+.2f}%）",
            f"- 深证成指：{real_data['深证成指']['close']:.0f}点（{real_data['深证成指']['change']:+.2f}%）",
            f"- 创业板指：{real_data['创业板指']['close']:.0f}点（{real_data['创业板指']['change']:+.2f}%）",
        ]
        data_summary = "\n".join(data_lines)
        data_note = f"""> **【数据说明】** 本报告基于以下真实市场数据生成：
> {data_summary}
> - 报告中的技术点位已根据真实数据进行校正

---

"""

        # 在第一个标题后插入
        content = re.sub(r'(^---\n\n)', f'\\1{data_note}', content, count=1, flags=re.MULTILINE)

        # 写回文件
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("\n✅ 报告数据已自动修正")
        print(f"   上证指数：{real_data['上证指数']['close']:.0f}点")
        print(f"   深证成指：{real_data['深证成指']['close']:.0f}点")
        print(f"   创业板指：{real_data['创业板指']['close']:.0f}点")

        # 保存分析结果到记忆系统
        print("\n💾 保存分析结果到记忆系统...")
        save_to_memory(content, today, memory_store)

        # 保存分析记录到历史系统
        print("\n📊 保存分析记录到历史系统...")
        from tradeclaw.memory.analysis_history import get_analysis_history
        from tradeclaw.tools.fetch_data import load_holdings

        analysis_history = get_analysis_history()
        holdings = load_holdings()
        current_holdings = holdings.get('current_holdings', [])
        closed_trades = holdings.get('closed_trades', [])

        # 提取持仓分析数据
        holdings_analysis_dict = {}
        for h in current_holdings:
            try:
                data = get_stock_data(h['code'], days=60)
                kline = data['indices']['kline'] if 'indices' in data else data.get('kline', [])
                if kline:
                    latest = kline[-1]
                    current_price = float(latest[5])
                    cost_price = h['cost']
                    change_pct = ((current_price - cost_price) / cost_price * 100)

                    # 技术分析
                    prices = [float(k[5]) for k in kline]
                    if len(kline) >= 20:
                        ma5 = sum([float(k[5]) for k in kline[-5:]]) / 5
                        ma20 = sum([float(k[5]) for k in kline[-20:]]) / 20
                        trend = 'up' if current_price > ma5 > ma20 else 'down' if current_price < ma5 < ma20 else 'sideways'
                    else:
                        trend = 'unknown'

                    holdings_analysis_dict[h['code']] = {
                        'name': h['name'],
                        'change_pct': change_pct,
                        'trend': trend,
                        'current_price': current_price,
                        'cost_price': cost_price
                    }
            except Exception as e:
                print(f"   分析 {h['code']} 失败: {e}")

        # 提取技术信号
        technical_signals = {
            'overall_trend': 'up' if real_data['上证指数']['change'] > 0 else 'down',
            'market_strength': 'strong' if abs(real_data['上证指数']['change']) > 1 else 'weak'
        }

        # 提取热点板块（从报告中）
        hot_sectors = []
        import re
        sector_pattern = r'【([^】]+)】|（([^）]+)）'
        matches = re.findall(sector_pattern, content)
        for match in matches:
            sector = match[0] if match[0] else match[1]
            if len(sector) < 10 and sector not in hot_sectors:
                hot_sectors.append(sector)

        # 生成标签
        tags = []
        sh_change = real_data['上证指数']['change']
        if sh_change > 0.5:
            tags.append('上涨')
        elif sh_change < -0.5:
            tags.append('下跌')
        else:
            tags.append('震荡')

        # 保存分析记录
        analysis_history.save_analysis(
            date=today,
            market_data=real_data,
            holdings_analysis=holdings_analysis_dict,
            technical_signals=technical_signals,
            hot_sectors=hot_sectors[:5],  # 保存前5个热点
            recommendations=content[-500:] if len(content) > 500 else content,  # 保存最后500字作为建议摘要
            tags=tags
        )

        # 历史交易复盘总结
        print("\n📈 历史交易复盘...")
        if closed_trades:
            profitable_count = sum(1 for t in closed_trades if '+' in str(t.get('profit', '')))
            total_count = len(closed_trades)
            win_rate = profitable_count / total_count if total_count > 0 else 0

            print(f"   总交易: {total_count} 笔")
            print(f"   盈利: {profitable_count} 笔")
            print(f"   亏损: {total_count - profitable_count} 笔")
            print(f"   胜率: {win_rate:.1%}")

            # 保存到记忆系统
            memory_store.add_reflection(
                insight=f"历史交易复盘 - {today}",
                conclusion=f"共{total_count}笔交易，胜率{win_rate:.1%}，盈利{profitable_count}笔，亏损{total_count - profitable_count}笔",
                confidence=0.8,
                scope=MemoryScope(),
                source_agent=AgentRole.TECHNICAL_ANALYST,
                tags=["历史交易", "胜率", "复盘"],
                lesson_learned="保持耐心，严格止损，顺势而为" if win_rate < 0.5 else "保持当前策略，继续执行"
            )

        # 记忆优化（自动提升高质量记忆、去重）
        print("\n🔧 优化记忆系统...")
        optimization_results = memory_optimizer.optimize_all(
            enable_promotion=True,   # 启用自动提升
            enable_dedup=True,       # 启用去重
            enable_cleanup=False     # 默认关闭自动清理
        )

        # 保存优化后的记忆
        memory_store.save(memory_dir)
        print("✅ 记忆优化完成并已保存")

        # 生成 PDF
        try:
            from md_to_pdf import convert_md_to_pdf
            pdf_path = report_path.replace('.md', '.pdf')
            convert_md_to_pdf(report_path, pdf_path)
        except Exception as e:
            print(f"\n⚠️ PDF生成失败: {e}")
    except Exception as e:
        print(f"\n⚠️ 报告后处理失败: {e}")
        import traceback
        traceback.print_exc()

    return result


def train():
    """训练crew"""
    inputs = {
        'topic': 'A股市场每日早报',
        'current_year': str(datetime.now().year)
    }
    try:
        Tradeclaw().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"训练时出错: {e}")


def replay():
    """回放之前的执行"""
    try:
        Tradeclaw().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"回放时出错: {e}")


def test():
    """测试crew"""
    inputs = {
        'topic': 'A股市场每日早报',
        'current_year': str(datetime.now().year)
    }
    try:
        Tradeclaw().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"测试时出错: {e}")


if __name__ == "__main__":
    run()
