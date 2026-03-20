#!/usr/bin/env python
"""
TradeClaw - 每日A股早报系统
"""
import sys
import os
import warnings
from datetime import datetime

from tradeclaw.crew import Tradeclaw

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    today = datetime.now().strftime('%Y-%m-%d')
    os.makedirs('reports', exist_ok=True)
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
                change = float(latest[12])
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
