"""
A股市场数据获取
使用东方财富免费API
"""

import requests
import json
from datetime import datetime
from typing import Optional
import os

# 禁用代理
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('ALL_PROXY', None)


def get_hot_sectors() -> list:
    """
    获取当日热点板块TOP15
    
    Returns:
        list: [{'name': '板块名', 'change': 涨跌幅, 'price': 最新价}, ...]
    """
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 30,
        "po": 1,  # 降序
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f3",  # 按涨跌幅排序
        "fs": "m:90+t:2",  # 行业板块
        "fields": "f2,f3,f4,f12,f14"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    # 禁用代理
    proxies = {"http": None, "https": None}
    resp = requests.get(url, params=params, headers=headers, timeout=10, proxies=proxies)
    data = resp.json()
    
    sectors = []
    if data.get('data') and data['data'].get('diff'):
        for item in data['data']['diff'][:15]:
            sectors.append({
                "name": item.get('f14', ''),
                "change": item.get('f3', 0),
                "price": item.get('f2', 0)
            })
    
    return sectors


def get_index_data() -> dict:
    """
    获取大盘指数数据
    
    Returns:
        dict: {'上证指数': {'price': xxx, 'change': xxx}, ...}
    """
    indices = {
        "sh.000001": "上证指数",
        "sz.399001": "深证成指",
        "sz.399006": "创业板指"
    }
    
    result = {}
    
    for code, name in indices.items():
        url = f"https://push2.eastmoney.com/api/qt/stock/get?fields=f43,f44,f45,f46,f47,f48,f169,f170,f171&secid={code}"
        
        try:
            proxies = {"http": None, "https": None}
            resp = requests.get(url, timeout=5, proxies=proxies)
            data = resp.json()
            
            if data.get('data'):
                d = data['data']
                result[name] = {
                    "price": d.get('f43', 0) / 1000 if d.get('f43') else 0,
                    "change": d.get('f44', 0) / 1000 if d.get('f44') else 0,
                    "open": d.get('f46', 0) / 1000 if d.get('f46') else 0,
                    "high": d.get('f44', 0) / 1000 if d.get('f44') else 0,
                    "low": d.get('f45', 0) / 1000 if d.get('f45') else 0,
                }
        except Exception as e:
            print(f"获取{name}失败: {e}")
            continue
    
    return result


def get_market_summary() -> dict:
    """
    获取市场涨跌统计
    
    Returns:
        dict: {'上涨': xxx, '下跌': xxx, '平盘': xxx}
    """
    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": 2,
        "fields": "f1,f2,f3,f4",
        "secids": "1.000001,0.399001"  # 沪市+深市
    }
    
    try:
        proxies = {"http": None, "https": None}
        resp = requests.get(url, params=params, timeout=10, proxies=proxies)
        data = resp.json()
        
        if data.get('data') and data['data'].get('diff'):
            up = down = flat = 0
            for item in data['data']['diff']:
                change = item.get('f2', 0)
                if change > 0:
                    up += 1
                elif change < 0:
                    down += 1
                else:
                    flat += 1
            
            return {"上涨": up, "下跌": down, "平盘": flat}
    except Exception as e:
        print(f"获取市场统计失败: {e}")
    
    return {"上涨": 0, "下跌": 0, "平盘": 0}


def get_market_data(date: Optional[str] = None) -> str:
    """
    获取完整的A股市场热点数据
    
    Args:
        date: 日期，格式 YYYY-MM-DD，默认今天
    
    Returns:
        str: 格式化的市场数据报告
    """
    
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    output = []
    
    # 1. 热点板块
    output.append(f"【A股市场热点数据 - {date}】\n")
    output.append("=" * 50)
    output.append("\n## 一、热点板块TOP15\n")
    
    sectors = get_hot_sectors()
    for i, s in enumerate(sectors, 1):
        change = s.get('change', 0)
        output.append(f"{i:2d}. {s['name']:<15} {change:+.2f}%")
    
    # 2. 大盘指数
    output.append("\n## 二、大盘指数\n")
    
    indices = get_index_data()
    for name, data in indices.items():
        change = data.get('change', 0)
        output.append(f"- {name}: {data.get('price'):.2f} ({change:+.2f}%)")
    
    # 3. 市场统计
    output.append("\n## 三、市场涨跌统计\n")
    
    summary = get_market_summary()
    output.append(f"- 上涨: {summary.get('上涨', 'N/A')} 家")
    output.append(f"- 下跌: {summary.get('下跌', 'N/A')} 家")
    output.append(f"- 平盘: {summary.get('平盘', 'N/A')} 家")
    
    return "\n".join(output)


# 测试
# if __name__ == "__main__":
#     print(get_market_data())
