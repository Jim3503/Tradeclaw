"""
报告后处理器
在报告生成后，用真实数据替换错误或编造的数字
"""
from tradeclaw.tools.fetch_data import get_stock_data
import re
from datetime import datetime


def fix_report_data(report_content: str) -> str:
    """
    修复报告中的数据，用真实数据替换错误的数字

    Args:
        report_content: 原始报告内容

    Returns:
        修复后的报告内容
    """
    # 获取真实数据
    real_data = {}
    for code, name in [("sh.000001", "上证指数"), ("sz.399001", "深证成指"), ("sz.399006", "创业板指")]:
        data = get_stock_data(code, days=30)
        kline = data['indices']['kline']
        if kline:
            latest = kline[-1]
            close_price = float(latest[5])
            change_pct = float(latest[12])
            high_price = float(latest[3])
            low_price = float(latest[4])
            real_data[name] = {
                'close': close_price,
                'change': change_pct,
                'high': high_price,
                'low': low_price,
                'date': latest[0]
            }

    # 计算支撑位和阻力位（基于当前价位的±3%-5%）
    for name, data in real_data.items():
        current = data['close']
        data['resistance'] = round(current * 1.03, 0)
        data['support'] = round(current * 0.97, 0)

    # 替换策略1：查找并替换明显错误的点位（如3050、3100等）
    # 使用正则表达式匹配常见的点位描述模式

    fixed_content = report_content

    # 首先替换区间描述（如3050-3150点）
    if real_data.get('上证指数'):
        sh_close = int(real_data['上证指数']['close'])
        # 替换上证指数的区间描述
        fixed_content = re.sub(
            r'(\d{3,4})\s*[-~－—到至]\s*(\d{3,4})\s*点(?:位)?',
            lambda m: f"{sh_close * 0.98:.0f}-{sh_close * 1.02:.0f}点" if int(m.group(1)) < 3500 else m.group(0),
            fixed_content
        )

    patterns_to_fix = [
        # 上证指数的错误点位
        (r'(上证指数[^。，]*?(?:约|大约|当前|收于|运行在|位于)?\s*)\d{3,4}\.?\d*\s*点',
         lambda m: f"{m.group(1)}约{int(real_data['上证指数']['close'])}点" if real_data.get('上证指数') else m.group(0)),

        # 深证成指的错误点位
        (r'(深证成指[^。，]*?(?:约|大约|当前|收于|运行在|位于)?\s*)\d{4,5}\.?\d*\s*点',
         lambda m: f"{m.group(1)}约{int(real_data['深证成指']['close'])}点" if real_data.get('深证成指') else m.group(0)),

        # 创业板指的错误点位
        (r'(创业板指[^。，]*?(?:约|大约|当前|收于|运行在|位于)?\s*)\d{3,4}\.?\d*\s*点',
         lambda m: f"{m.group(1)}约{int(real_data['创业板指']['close'])}点" if real_data.get('创业板指') else m.group(0)),
    ]

    fixed_content = report_content
    for pattern, replacer in patterns_to_fix:
        fixed_content = re.sub(pattern, replacer, fixed_content, flags=re.IGNORECASE)

    # 替换策略2：添加真实数据摘要到报告顶部
    data_summary = f"""
> **【数据更正】** 本报告使用以下真实市场数据进行分析：
> - 上证指数：当前 {real_data['上证指数']['close']:.0f} 点（涨跌 {real_data['上证指数']['change']:+.2f}%）
> - 深证成指：当前 {real_data['深证成指']['close']:.0f} 点（涨跌 {real_data['深证成指']['change']:+.2f}%）
> - 创业板指：当前 {real_data['创业板指']['close']:.0f} 点（涨跌 {real_data['创业板指']['change']:+.2f}%）
> - 数据日期：{real_data['上证指数']['date']}

---

"""

    # 在第一个标题后插入数据摘要
    fixed_content = re.sub(
        r'(---\n\n##)',
        f'\\1{data_summary}',
        fixed_content,
        count=1
    )

    return fixed_content


if __name__ == "__main__":
    # 测试
    test_report = """
# A股市场每日早报

## 今日市场概览

综合分析，今日A股市场...

## 技术面分析

上证指数目前在3050-3150点区间震荡，昨日收于3088点。
深证成指运行在10000点附近。
创业板指在1850点争夺。
"""
    print("=== 原始报告 ===")
    print(test_report)
    print("\n=== 修复后报告 ===")
    print(fix_report_data(test_report))
