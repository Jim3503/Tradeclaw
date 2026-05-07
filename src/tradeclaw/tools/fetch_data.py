from unittest import result
import baostock as bs
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Dict,List,Any,Optional
import requests
from numpy import row_stack
import os
import yaml

# 禁用代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)


def load_holdings() -> dict:
    """从配置文件加载持仓数据"""
    # 固定路径
    config_path = "/home/ming/ai-projects/daily-report/tradeclaw/config/holdings.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def Norm_stock_code(code:str) -> dict:
    code = code.strip()
    if code.startswith("sh.") or code.startswith("sz."):
        return code
    if code.startswith("6"):
        return f"sh.{code}"
    else:
        return f"sz.{code}"


def get_stock_data(code:str,days:int = 30, use_cache:bool = True) -> dict :
    """
    获取A股市场的数据 - 优先使用AkShare，支持K线缓存

    Args:
        code: 股票代码
        days: 获取天数
        use_cache: 是否使用缓存（默认True）

    Returns:
        数据字典
    """

    # 1️⃣ 尝试从缓存读取
    cached_kline = None
    cache_latest_date = None

    if use_cache:
        from tradeclaw.data.kline_cache import get_kline_cache
        cache = get_kline_cache()
        cached_kline = cache.get_cached_kline(code)

        if cached_kline:
            cache_latest_date = cached_kline[-1][0]
            print(f"📦 缓存最新日期: {cache_latest_date}")

    # 2️⃣ 获取新数据（优先使用AkShare）
    try:
        from tradeclaw.data.akshare_data import get_stock_kline_akshare, get_stock_realtime_akshare
        from tradeclaw.data.kline_cache import get_kline_cache

        # 获取历史K线数据
        new_kline_data = get_stock_kline_akshare(code, days=days)

        if new_kline_data:
            # 3️⃣ 合并缓存和新数据
            if cached_kline and use_cache:
                cache = get_kline_cache()
                kline_data = cache.merge_kline(cached_kline, new_kline_data)

                # 保存到缓存
                cache.save_kline(code, kline_data, data_source='akshare')
            else:
                kline_data = new_kline_data

                # 保存到缓存
                if use_cache:
                    cache = get_kline_cache()
                    cache.save_kline(code, kline_data, data_source='akshare')

            print(f"✅ AkShare成功获取 {code} 的 {len(kline_data)} 条K线数据")

            # 尝试获取实时数据（使用新浪API，速度快）
            realtime_data = None
            try:
                from tradeclaw.data.hybrid_data import get_realtime_quote_sina
                sina_code = code.replace('.', '')
                realtime_data = get_realtime_quote_sina(sina_code)
            except:
                pass

            return {
                'indices': {
                    'stock_code': code,
                    'days': days,
                    'start_date': kline_data[0][0] if kline_data else '',
                    'end_date': kline_data[-1][0] if kline_data else '',
                    'kline': kline_data
                },
                'realtime': realtime_data,
                'data_source': 'akshare_primary'
            }
        else:
            print(f"⚠️ AkShare未获取到 {code} 的数据，尝试混合数据源...")

    except Exception as e:
        print(f"AkShare获取 {code} 失败: {e}，尝试混合数据源...")
        import traceback
        traceback.print_exc()

    # 4️⃣ 备用方案：使用混合数据源（新浪实时API + baostock历史数据）
    try:
        from tradeclaw.data.hybrid_data import get_stock_data_hybrid
        result = get_stock_data_hybrid(code, days)

        # 转换为兼容格式
        if result.get('kline'):
            # 合并缓存
            if cached_kline and use_cache:
                from tradeclaw.data.kline_cache import get_kline_cache
                cache = get_kline_cache()
                merged_kline = cache.merge_kline(cached_kline, result['kline'])
                cache.save_kline(code, merged_kline, data_source='hybrid')
                result['kline'] = merged_kline

            return {
                'indices': {
                    'stock_code': result['code'],
                    'days': days,
                    'start_date': result['kline'][0][0] if result['kline'] else '',
                    'end_date': result['kline'][-1][0] if result['kline'] else '',
                    'kline': result['kline']
                },
                'realtime': result.get('realtime'),
                'data_source': result.get('data_source', 'hybrid')
            }
    except Exception as e:
        print(f"混合数据源也失败，回退到baostock: {e}")

    # 最后回退到原始的baostock方法
    lg = bs.login()
    data ={}
    data['indices'] = get_indices(code,days)
    bs.logout()
    return data


def get_market_data() ->dict:
    """获取A股市场热点数据"""
    
    result = []
    
    # 1. 获取板块涨跌榜
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 50,
        "po": 1,  # 降序
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",  # 按涨跌幅排序
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f1,f2,f3,f4,f12,f13,f14"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    proxies = {"http": None, "https": None}
    resp = requests.get(url, params=params, headers=headers, timeout=10, proxies=proxies)
    data = resp.json()
    
    result.append("【当日热点板块TOP10】")
    if data.get('data') and data['data'].get('diff'):
        for i, item in enumerate(data['data']['diff'][:10], 1):
            name = item.get('f14', '')
            change = item.get('f3', 0)
            result.append(f"{i}. {name} ({change:+.2f}%)")
    
    # 2. 获取大盘指数
    result.append("\n【大盘指数】")
    indices = [
        ("sh.000001", "上证指数"),
        ("sz.399001", "深证成指"),
        ("sz.399006", "创业板指")
    ]
    
    for code, name in indices:
        url = f"https://push2ex.eastmoney.com/getTopicZDFenBu?ut=7eea3edcaed734bea9cbfc24409ed989&dession=01&mession=01"
        # 简化：直接返回指数代码
        result.append(f"- {name}: {code}")
    
    return "\n".join(result)

def get_indices(code:str,days:int=30) -> dict:
    """ 获取大盘指数"""
    bs_code = Norm_stock_code(code)
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    rs = bs.query_history_k_data_plus(bs_code,
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
    start_date, end_date, frequency="d", adjustflag="3")
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    return {
        "stock_code": bs_code,
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
        "kline": data_list
    }

# if __name__ =="__main__":
#     result = get_stock_data("000001",30)
#     print(result)


 
    
    