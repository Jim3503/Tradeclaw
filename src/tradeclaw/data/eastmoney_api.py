"""
东方财富API数据获取
免费、无需注册、支持ETF和个股
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any


def get_stock_kline_eastmoney(code: str, days: int = 60) -> List[List]:
    """
    使用东方财富API获取K线数据（支持ETF和个股）
    
    Args:
        code: 股票代码，如 '600150', '513310', '601899'
        days: 获取天数
        
    Returns:
        K线数据列表，格式: [日期, 代码, 开盘, 最高, 最低, 收盘, 成交量, 成交额]
    """
    try:
        # 标准化代码格式
        code = code.strip().replace('.', '').replace('sh', '').replace('sz', '')

        # 特殊处理指数代码（必须在个股判断之前）
        if code in ['000001']:  # 上证指数
            secid = f"1.{code}"  # 上证指数使用1.前缀
        elif code in ['399001', '399006', '399102', '399905']:  # 深证指数
            secid = f"0.{code}"  # 深证指数使用0.前缀
        # 判断市场和证券类型
        elif code.startswith('6'):
            secid = f"1.{code}"  # 上海A股
        elif code.startswith('0') or code.startswith('3'):
            secid = f"0.{code}"  # 深圳A股
        elif code.startswith('5'):
            secid = f"1.{code}"  # 上海ETF/基金
        else:
            secid = f"0.{code}"  # 默认深圳
        
        # 东方财富K线API
        url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
        
        # 计算开始日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days+30)  # 多取一些确保有足够数据
        
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日K线
            'fqt': '0',    # 不复权
            'beg': start_date.strftime('%Y%m%d'),
            'end': end_date.strftime('%Y%m%d'),
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"东财API获取{code}失败: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        if data.get('rc') != 0 or not data.get('data'):
            print(f"东财API返回{code}数据为空")
            return []
        
        kline_items = data['data'].get('klines', [])
        
        if not kline_items:
            print(f"东财API返回{code}的K线数据为空")
            return []
        
        # 只取最近days天
        kline_items = kline_items[-days:]
        
        # 转换为标准格式
        result = []
        for item in kline_items:
            # 格式: "2026-05-07,32.91,32.95,32.50,32.69,411759,1356105360.00"
            parts = item.split(',')
            if len(parts) >= 6:
                result.append([
                    parts[0],        # 日期
                    code,            # 代码
                    float(parts[1]), # 开盘
                    float(parts[3]), # 最高
                    float(parts[4]), # 最低
                    float(parts[2]), # 收盘
                    float(parts[5]), # 成交量
                    float(parts[6]) if len(parts) > 6 else 0  # 成交额
                ])
        
        print(f"✅ 东财API成功获取 {code} 的 {len(result)} 条K线数据")
        return result
        
    except Exception as e:
        print(f"东财API获取{code}失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_stock_realtime_eastmoney(code: str) -> Dict[str, Any]:
    """
    使用东方财富API获取实时行情
    
    Args:
        code: 股票代码
        
    Returns:
        实时行情数据字典
    """
    try:
        # 标准化代码
        code = code.strip().replace('.', '').replace('sh', '').replace('sz', '')
        
        # 判断市场
        if code.startswith('6') or code.startswith('5'):
            secid = f"1.{code}"
        else:
            secid = f"0.{code}"
        
        # 东方财富实时行情API
        url = "http://push2.eastmoney.com/api/qt/stock/get"
        params = {
            'secid': secid,
            'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f107,f116,f117,f127,f152,f161,f162,f167,f168,f169,f170,f171,f84,f85',
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://quote.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('rc') == 0 and data.get('data'):
                info = data['data']
                return {
                    'name': info.get('f58', ''),
                    'code': code,
                    'price': info.get('f43', 0) / 100 if info.get('f43') else 0,  # 价格需要除以100
                    'open': info.get('f46', 0) / 100 if info.get('f46') else 0,
                    'high': info.get('f44', 0) / 100 if info.get('f44') else 0,
                    'low': info.get('f45', 0) / 100 if info.get('f45') else 0,
                    'pre_close': info.get('f60', 0) / 100 if info.get('f60') else 0,
                    'volume': info.get('f47', 0) if info.get('f47') else 0,
                    'amount': info.get('f48', 0) if info.get('f48') else 0,
                    'change_pct': info.get('f170', 0) / 100 if info.get('f170') else 0,  # 涨跌幅
                    'source': 'eastmoney_realtime'
                }
        
        return None
        
    except Exception as e:
        print(f"东财API获取{code}实时行情失败: {e}")
        return None


def test_eastmoney_api():
    """测试东方财富API"""
    print("=" * 60)
    print("测试东方财富API（免费、无需注册、支持ETF）")
    print("=" * 60)
    
    test_cases = [
        ('600150', '中国船舶'),
        ('513310', '中韩半导体ETF'),
        ('601899', '紫金矿业'),
        ('000657', '中钨高新'),
    ]
    
    for code, name in test_cases:
        print(f"\n测试 {name}({code})...")
        
        # 测试K线数据
        kline = get_stock_kline_eastmoney(code, days=10)
        if kline:
            print(f"  ✅ K线: {len(kline)}条")
            print(f"  最新: {kline[-1][0]} | 收盘: {kline[-1][5]}")
        else:
            print(f"  ❌ K线数据获取失败")
        
        # 测试实时数据
        realtime = get_stock_realtime_eastmoney(code)
        if realtime:
            print(f"  ✅ 实时: {realtime['price']:.2f} ({realtime['change_pct']:+.2f}%)")
        else:
            print(f"  ❌ 实时数据获取失败")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_eastmoney_api()
