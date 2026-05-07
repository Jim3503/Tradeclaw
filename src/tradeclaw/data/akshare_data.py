"""
使用 AkShare 获取A股数据
替代不稳定的东方财富API
"""
import akshare as ak
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd


def get_hot_sectors_akshare(limit: int = 10) -> List[Dict[str, Any]]:
    """
    使用 AkShare 获取热点板块数据

    Args:
        limit: 返回板块数量

    Returns:
        板块数据列表
    """
    try:
        # 获取概念板块行情
        df = ak.stock_board_concept_name_em()

        if df is None or df.empty:
            print("AkShare: 未获取到概念板块数据")
            return []

        # 按涨跌幅排序，取前N个
        df = df.sort_values('涨跌幅', ascending=False).head(limit)

        sectors = []
        for _, row in df.iterrows():
            sectors.append({
                'name': row['板块名称'],
                'change_pct': row['涨跌幅'],
                'leader': row['最新价'],  # 使用最新价代替
                'description': row['板块名称']
            })

        return sectors

    except Exception as e:
        print(f"AkShare 获取热点板块失败: {e}")
        return []


def get_market_indices_akshare() -> Dict[str, Any]:
    """
    使用 AkShare 获取大盘指数数据

    Returns:
        指数数据字典
    """
    try:
        # 使用新浪财经API获取指数数据（更稳定）
        indices = {}

        target_indices = [
            ('sh000001', '上证指数'),
            ('sz399001', '深证成指'),
            ('sz399006', '创业板指')
        ]

        for code, name in target_indices:
            try:
                # 使用新浪API
                url = f'https://hq.sinajs.cn/list={code}'
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://finance.sina.com.cn'
                }
                resp = requests.get(url, headers=headers, timeout=5)

                if resp.status_code == 200:
                    content = resp.text
                    start = content.find('"')
                    end = content.rfind('"')

                    if start > 0 and end > start:
                        data_str = content[start+1:end]
                        parts = data_str.split(',')

                        if len(parts) > 30:
                            indices[name] = {
                                'name': name,
                                'code': code,
                                'current': float(parts[3]) if parts[3] else 0,
                                'change_pct': ((float(parts[3]) - float(parts[2])) / float(parts[2]) * 100) if parts[2] and parts[3] else 0,
                                'open': float(parts[1]) if parts[1] else 0,
                                'high': float(parts[4]) if parts[4] else 0,
                                'low': float(parts[5]) if parts[5] else 0,
                                'volume': float(parts[8]) if parts[8] else 0,
                                'amount': float(parts[9]) if parts[9] else 0
                            }

            except Exception as e:
                print(f"获取 {name} 失败: {e}")
                continue

        return indices

    except Exception as e:
        print(f"AkShare 获取指数数据失败: {e}")
        return {}


def get_stock_kline_akshare(code: str, days: int = 60) -> List[List]:
    """
    使用 AkShare 获取股票K线数据

    Args:
        code: 股票代码，如 '601611', 'sh000001', 'sh.000001'
        days: 获取天数

    Returns:
        K线数据列表，格式与baostock一致
    """
    try:
        # 转换代码格式：支持多种输入格式
        # 'sh000001' -> '000001' (上证指数)
        # 'sz399001' -> '399001' (深证成指)
        # 'sh.000001' -> '000001'
        # '601611' -> '601611'

        code = code.strip()
        if '.' in code:
            code = code.split('.')[-1]
        elif code.startswith('sh') or code.startswith('sz'):
            code = code[2:]  # 去掉sh/sz前缀

        # 对于指数，优先使用东方财富API（快速、准确）
        if code in ['000001', '399001', '399006']:
            try:
                from tradeclaw.data.eastmoney_api import get_stock_kline_eastmoney
                print(f"AkShare检测到指数代码{code}，调用东财API...")
                return get_stock_kline_eastmoney(code, days=days)
            except Exception as e:
                print(f"东财API获取指数{code}失败，尝试AkShare: {e}")
                # 回退到AkShare
                try:
                    df = ak.index_zh_a_hist(symbol=code, period='daily')
                    if df is not None and not df.empty:
                        df = df.tail(days)
                        kline_data = []
                        for _, row in df.iterrows():
                            date_str = row['日期']
                            kline_data.append([
                                date_str, code, row['开盘'], row['最高'],
                                row['最低'], row['收盘'], row['成交量'], row['成交额']
                            ])
                        print(f"✅ AkShare成功获取指数{code}的{len(kline_data)}条K线数据")
                        return kline_data
                except Exception as e2:
                    print(f"AkShare也失败: {e2}")
                    return []
        else:
            # ETF优先使用东方财富API
            if code.startswith('5'):
                from tradeclaw.data.eastmoney_api import get_stock_kline_eastmoney
                print(f"AkShare检测到ETF代码{code}，调用东财API...")
                return get_stock_kline_eastmoney(code, days=days)

            # 个股使用stock_zh_a_hist
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=(datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d'), adjust="")

            if df is None or df.empty:
                print(f"AkShare: 未获取到股票 {code} 的K线数据，尝试东财API...")
                # 回退到东方财富API
                from tradeclaw.data.eastmoney_api import get_stock_kline_eastmoney
                return get_stock_kline_eastmoney(code, days=days)

            # 只取最近days天
            df = df.tail(days)

            # 转换为baostock格式
            # baostock格式: date, code, open, high, low, close, volume, amount
            kline_data = []
            for _, row in df.iterrows():
                kline_data.append([
                    row['日期'].strftime('%Y-%m-%d'),  # 日期
                    code,  # 代码
                    row['开盘'],  # open
                    row['最高'],  # high
                    row['最低'],  # low
                    row['收盘'],  # close
                    row['成交量'],  # volume
                    row['成交额']  # amount
                ])

            return kline_data

        # 获取历史数据
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=(datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d'), adjust="")

        if df is None or df.empty:
            print(f"AkShare: 未获取到股票 {code} 的K线数据")
            return []

        # 只取最近days天
        df = df.tail(days)

        # 转换为baostock格式
        # baostock格式: date, code, open, high, low, close, volume, amount
        kline_data = []
        for _, row in df.iterrows():
            kline_data.append([
                row['日期'].strftime('%Y-%m-%d'),  # 日期
                code,  # 代码
                row['开盘'],  # open
                row['最高'],  # high
                row['最低'],  # low
                row['收盘'],  # close
                row['成交量'],  # volume
                row['成交额']  # amount
            ])

        return kline_data

    except Exception as e:
        print(f"AkShare 获取股票 {code} K线失败: {e}")
        return []


def get_stock_realtime_akshare(code: str) -> Optional[Dict]:
    """
    使用 AkShare 获取个股实时行情

    Args:
        code: 股票代码

    Returns:
        实时行情数据
    """
    try:
        # 转换代码格式
        if '.' in code:
            code = code.split('.')[-1]

        # 获取实时行情
        df = ak.stock_zh_a_spot_em()

        if df is None or df.empty:
            return None

        row = df[df['代码'] == code]
        if row.empty:
            return None

        row = row.iloc[0]
        return {
            'name': row['名称'],
            'code': code,
            'current': row['最新价'],
            'open': row['今开'],
            'high': row['最高'],
            'low': row['最低'],
            'volume': row['成交量'],
            'amount': row['成交额'],
            'change_pct': row['涨跌幅']
        }

    except Exception as e:
        print(f"AkShare 获取 {code} 实时行情失败: {e}")
        return None


def test_akshare():
    """测试 AkShare 数据获取"""
    print("="*50)
    print("测试 AkShare 数据获取")
    print("="*50)

    # 测试1: 热点板块
    print("\n1️⃣ 测试热点板块...")
    sectors = get_hot_sectors_akshare(limit=5)
    if sectors:
        print(f"   ✅ 获取到 {len(sectors)} 个热点板块:")
        for s in sectors[:3]:
            print(f"   - {s['name']}: {s['change_pct']:+.2f}%")

    # 测试2: 大盘指数
    print("\n2️⃣ 测试大盘指数...")
    indices = get_market_indices_akshare()
    if indices:
        print(f"   ✅ 获取到 {len(indices)} 个指数:")
        for name, data in indices.items():
            print(f"   - {name}: {data['current']:.0f} ({data['change_pct']:+.2f}%)")

    # 测试3: 个股K线
    print("\n3️⃣ 测试个股K线（中国核建）...")
    kline = get_stock_kline_akshare('601611', days=10)
    if kline:
        print(f"   ✅ 获取到 {len(kline)} 天K线数据")
        print(f"   最新: {kline[-1][5]} 元 ({kline[-1][0]})")

    print("\n" + "="*50)
    print("✅ AkShare 测试完成")
    print("="*50)


if __name__ == "__main__":
    test_akshare()
