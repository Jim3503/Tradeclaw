"""
实时A股数据获取 - 使用东方财富API
"""
import requests
import os
from datetime import datetime

# 禁用代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)


def get_realtime_index(index_code: str) -> dict:
    """
    获取指数实时数据

    Args:
        index_code: 指数代码，如 'sh.000001'（上证指数）、'sz.399006'（创业板指）

    Returns:
        dict: 包含实时价格、涨跌幅等信息的字典
    """
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": index_code,
        "fields": "f43,f44,f45,f46,f47,f48,f60,f170,f171"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    proxies = {"http": None, "https": None}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10, proxies=proxies)
        data = resp.json()

        if data.get('data') and data['rc'] == 0:
            d = data['data']
            return {
                'name': d.get('f58', ''),
                'code': index_code,
                'price': d.get('f43', 0) / 1000 if d.get('f43') else 0,  # 最新价
                'change_pct': d.get('f44', 0) / 100 if d.get('f44') else 0,  # 涨跌幅
                'change_amt': d.get('f169', 0) / 100 if d.get('f169') else 0,  # 涨跌额
                'open': d.get('f46', 0) / 1000 if d.get('f46') else 0,  # 开盘价
                'pre_close': d.get('f60', 0) / 1000 if d.get('f60') else 0,  # 昨收价
                'high': d.get('f47', 0) / 1000 if d.get('f47') else 0,  # 最高价
                'low': d.get('f48', 0) / 1000 if d.get('f48') else 0,  # 最低价
                'volume': d.get('f47', 0),  # 成交量（手）
                'amount': d.get('f48', 0),  # 成交额
                'update_time': d.get('f171', ''),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    except Exception as e:
        print(f"获取{index_code}实时数据失败: {e}")
        return None


def get_all_indices_realtime() -> dict:
    """
    获取三大指数的实时数据

    Returns:
        dict: 包含上证指数、深证成指、创业板指的实时数据
    """
    indices = {
        "sh.000001": "上证指数",
        "sz.399001": "深证成指",
        "sz.399006": "创业板指"
    }

    result = {}
    for code, name in indices.items():
        data = get_realtime_index(code)
        if data:
            result[name] = data
            print(f"✓ {name}: {data['price']:.2f}点 ({data['change_pct']:+.2f}%)")
        else:
            print(f"✗ {name}: 获取失败")

    return result


def get_realtime_hot_sectors(limit: int = 15) -> list:
    """
    获取实时热点板块

    Args:
        limit: 返回板块数量

    Returns:
        list: 热点板块列表
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": limit,
        "po": 1,  # 降序
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",  # 按涨跌幅排序
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f2,f3,f4,f12,f14"
    }

    headers = {"User-Agent": "Mozilla/5.0"}
    proxies = {"http": None, "https": None}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10, proxies=proxies)
        data = resp.json()

        sectors = []
        if data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff'][:limit]:
                sectors.append({
                    "name": item.get('f14', ''),
                    "change": item.get('f3', 0),
                    "price": item.get('f2', 0)
                })
        return sectors
    except Exception as e:
        print(f"获取热点板块失败: {e}")
        return []


if __name__ == "__main__":
    print("=" * 50)
    print("测试实时数据获取")
    print("=" * 50)

    print("\n【三大指数实时数据】")
    indices = get_all_indices_realtime()

    print("\n【热点板块TOP5】")
    sectors = get_realtime_hot_sectors(5)
    for i, s in enumerate(sectors, 1):
        print(f"{i}. {s['name']}: {s['change']:+.2f}%")
