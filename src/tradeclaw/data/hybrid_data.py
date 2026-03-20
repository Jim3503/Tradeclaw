"""
混合数据源 - 实时数据 + 历史数据
优先使用实时API，失败时回退到baostock
"""
import requests
import baostock as bs
from datetime import datetime, timedelta
import os

# 禁用代理
for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)


def get_realtime_quote_sina(code: str) -> dict:
    """
    使用新浪财经API获取实时行情（不需要token，速度快）

    Args:
        code: 如 'sh000001', 'sz399006'（注意格式，不需要点）

    Returns:
        dict: 实时行情数据
    """
    # 新浪财经实时行情API
    url = f'https://hq.sinajs.cn/list={code}'

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn'
        }
        resp = requests.get(url, headers=headers, timeout=5)

        if resp.status_code == 200:
            # 解析响应: var hq_str_sh000001="上证指数,4050.51,3923.47,4054.11,..."
            content = resp.text
            start = content.find('"')
            end = content.rfind('"')
            if start > 0 and end > start:
                data_str = content[start+1:end]
                parts = data_str.split(',')

                if len(parts) > 30:  # 确保数据完整
                    name = parts[0]
                    open_p = float(parts[1]) if parts[1] else 0
                    pre_close = float(parts[2]) if parts[2] else 0
                    price = float(parts[3]) if parts[3] else 0
                    high = float(parts[4]) if parts[4] else 0
                    low = float(parts[5]) if parts[5] else 0
                    volume = float(parts[8]) if parts[8] else 0
                    amount = float(parts[9]) if parts[9] else 0

                    # 计算涨跌幅
                    change_pct = ((price - pre_close) / pre_close * 100) if pre_close > 0 else 0

                    return {
                        'name': name,
                        'code': code,
                        'price': price,
                        'open': open_p,
                        'pre_close': pre_close,
                        'high': high,
                        'low': low,
                        'change_pct': change_pct,
                        'volume': volume,
                        'amount': amount,
                        'source': 'sina_realtime',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
    except Exception as e:
        print(f"新浪API获取{code}失败: {e}")

    return None


def get_stock_data_hybrid(code: str, days: int = 30) -> dict:
    """
    混合数据获取：优先实时API，回退到baostock

    Args:
        code: 股票/指数代码，支持 'sh.000001' 或 'sh000001' 格式
        days: 获取历史数据天数

    Returns:
        dict: 包含实时数据和历史K线的字典
    """
    # 标准化代码格式
    code = code.strip().replace('.', '')

    # 特殊处理ETF代码：5开头的通常是上海ETF
    if code.startswith('5') and len(code) == 6:
        code = 'sh' + code
    elif code.startswith('6'):
        code = 'sh' + code
    elif code.startswith('0') or code.startswith('3'):
        code = 'sz' + code
    elif not code.startswith('sh') and not code.startswith('sz'):
        # 如果已经有sh/sz前缀，保持原样
        pass

    # 先尝试获取实时数据
    realtime_data = get_realtime_quote_sina(code)

    # 获取历史数据（baostock）
    bs_code = f"{code[:2]}.{code[2:]}"  # 转换为 baostock 格式
    lg = bs.login()

    kline_data = []
    if lg.error_code == '0':
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')

        rs = bs.query_history_k_data_plus(
            bs_code,
            'date,code,open,high,low,close,preclose,volume,amount,pctChg,turn,tradestatus,pctChg,isST',
            start_date, end_date,
            frequency='d', adjustflag='3'
        )

        while (rs.error_code == '0') & rs.next():
            kline_data.append(rs.get_row_data())

    bs.logout()

    # 如果有实时数据，更新/添加到K线中
    if realtime_data:
        today_str = datetime.now().strftime('%Y-%m-%d')
        # 检查今天是否已在K线中
        today_exists = any(k[0] == today_str for k in kline_data)

        if not today_exists and realtime_data['price'] > 0:
            # 添加今天的实时数据到K线
            kline_entry = [
                today_str,
                bs_code,
                str(realtime_data['open']),
                str(realtime_data['high']),
                str(realtime_data['low']),
                str(realtime_data['price']),
                str(realtime_data['pre_close']),
                str(realtime_data['volume']),
                str(realtime_data['amount']),
                '3',
                str(realtime_data.get('turn', 0)),
                '1',
                str(realtime_data['change_pct']),
                '0'
            ]
            kline_data.append(kline_entry)

    return {
        'code': bs_code,
        'realtime': realtime_data,
        'kline': kline_data,
        'data_source': 'sina_realtime' if realtime_data else 'baostock_historical'
    }


def get_all_indices_hybrid() -> dict:
    """
    获取三大指数的混合数据

    Returns:
        dict: 包含上证指数、深证成指、创业板指的数据
    """
    indices = {
        "sh.000001": "上证指数",
        "sz.399001": "深证成指",
        "sz.399006": "创业板指"
    }

    result = {}
    for code, name in indices.items():
        print(f"正在获取 {name}...")
        data = get_stock_data_hybrid(code, days=30)

        if data.get('realtime'):
            rt = data['realtime']
            print(f"  ✓ {name}: {rt['price']:.2f}点 ({rt['change_pct']:+.2f}%) [实时]")
        else:
            # 使用历史数据最新一条
            kline = data.get('kline', [])
            if kline:
                latest = kline[-1]
                print(f"  ⚠ {name}: {latest[5]}点 (历史数据: {latest[0]})")

        result[name] = data

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("测试混合数据源")
    print("=" * 60)

    print("\n【获取三大指数数据】")
    indices_data = get_all_indices_hybrid()

    print("\n【详细数据】")
    for name, data in indices_data.items():
        print(f"\n{name}:")
        if data.get('realtime'):
            rt = data['realtime']
            print(f"  实时价格: {rt['price']:.2f}")
            print(f"  涨跌幅: {rt['change_pct']:+.2f}%")
            print(f"  开盘: {rt['open']:.2f}")
            print(f"  最高: {rt['high']:.2f}")
            print(f"  最低: {rt['low']:.2f}")

        kline = data.get('kline', [])
        if kline:
            print(f"  K线数据: {len(kline)} 条")
            print(f"  最新: {kline[-1][0]} {kline[-1][5]}点")
