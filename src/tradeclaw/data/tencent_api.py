"""
腾讯财经API数据获取
免费、无需注册、支持ETF
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pandas as pd


def get_stock_kline_tencent(code: str, days: int = 60) -> List[List]:
    """
    使用腾讯财经API获取K线数据（支持ETF）
    
    Args:
        code: 股票代码，如 'sh600150', 'sz513310'
        days: 获取天数
        
    Returns:
        K线数据列表，格式: [日期, 代码, 开盘, 最高, 最低, 收盘, 成交量, 成交额]
    """
    try:
        # 标准化代码格式
        code = code.strip().replace('.', '')
        
        # 判断市场
        if code.startswith('6') or code.startswith('5') or code == '000001':
            market = 'sh'  # 上海市场
        else:
            market = 'sz'  # 深圳市场
            
        symbol = f"{market}{code}"
        
        # 获取K线数据（日K线）
        # 腾讯API格式: http://web.ifzq.gtimg.cn/appstock/app/fqkline/get...
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            'param': f"{symbol},day,{days}",
            '_var': f"kline_{symbol}day",
            '_dev': 'false',
            '_sort': 'false',
            '_token': '',
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://stockapp.finance.qq.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"腾讯API获取{code}失败: HTTP {response.status_code}")
            return []
        
        # 解析响应 (JavaScript格式)
        content = response.text
        # 移除前面的var kline_xxx= 和后面的;
        start = content.find('{')
        end = content.rfind('}') + 1
        
        if start < 0 or end <= start:
            print(f"腾讯API返回格式错误: {code}")
            return []
        
        import json
        data = json.loads(content[start:end])
        
        # 提取K线数据
        if 'data' not in data or symbol not in data['data']:
            print(f"腾讯API未包含{code}的数据")
            return []
        
        kline_list = data['data'][symbol]['day']
        
        if not kline_list:
            print(f"腾讯API返回{code}的K线数据为空")
            return []
        
        # 转换为标准格式: [日期, 代码, 开, 高, 低, 收, 量, 额]
        result = []
        for item in kline_list[:days]:  # 只取最近days天
            # 腾讯API格式: [日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额]
            # 日期格式: 20260507
            date_str = str(item[0])
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            result.append([
                formatted_date,    # 日期
                code,              # 代码
                item[1],           # 开盘
                item[3],           # 最高
                item[4],           # 最低
                item[2],           # 收盘
                item[5],           # 成交量
                item[6] if len(item) > 6 else 0  # 成交额
            ])
        
        print(f"✅ 腾讯API成功获取 {code} 的 {len(result)} 条K线数据")
        return result
        
    except Exception as e:
        print(f"腾讯API获取{code}失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_stock_realtime_tencent(code: str) -> Dict[str, Any]:
    """
    使用腾讯财经API获取实时行情
    
    Args:
        code: 股票代码
        
    Returns:
        实时行情数据字典
    """
    try:
        # 标准化代码
        code = code.strip().replace('.', '')
        
        if code.startswith('6') or code.startswith('5'):
            market = 'sh'
        else:
            market = 'sz'
            
        symbol = f"{market}{code}"
        
        # 腾讯实时行情API
        url = f"http://qt.gtimg.cn/q={symbol}"
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'http://stockapp.finance.qq.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            content = response.text
            # 解析格式: v_sh600150="中国船舶~..."
            start = content.find('"')
            end = content.rfind('"')
            
            if start > 0 and end > start:
                data_str = content[start+1:end]
                parts = data_str.split('~')
                
                if len(parts) > 30:
                    return {
                        'name': parts[1],
                        'code': code,
                        'price': float(parts[3]) if parts[3] else 0,
                        'open': float(parts[5]) if len(parts) > 5 and parts[5] else 0,
                        'high': float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                        'low': float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                        'pre_close': float(parts[4]) if parts[4] else 0,
                        'volume': float(parts[36]) if len(parts) > 36 and parts[36] else 0,
                        'amount': float(parts[37]) if len(parts) > 37 and parts[37] else 0,
                        'change_pct': ((float(parts[3]) - float(parts[4])) / float(parts[4]) * 100) if parts[3] and parts[4] and float(parts[4]) > 0 else 0,
                        'source': 'tencent_realtime'
                    }
        
        return None
        
    except Exception as e:
        print(f"腾讯API获取{code}实时行情失败: {e}")
        return None


def test_tencent_api():
    """测试腾讯财经API"""
    print("=" * 60)
    print("测试腾讯财经API（免费、无需注册）")
    print("=" * 60)
    
    test_cases = [
        ('sh600150', '中国船舶'),
        ('sh513310', '中韩半导体ETF'),
        ('sh601899', '紫金矿业'),
        ('sz000657', '中钨高新'),
    ]
    
    for code, name in test_cases:
        print(f"\n测试 {name}({code})...")
        
        # 测试K线数据
        kline = get_stock_kline_tencent(code, days=10)
        if kline:
            print(f"  ✅ K线: {len(kline)}条")
            print(f"  最新: {kline[-1][0]} | 收盘: {kline[-1][5]}")
        else:
            print(f"  ❌ K线数据获取失败")
        
        # 测试实时数据
        realtime = get_stock_realtime_tencent(code)
        if realtime:
            print(f"  ✅ 实时: {realtime['price']:.2f} ({realtime['change_pct']:+.2f}%)")
        else:
            print(f"  ❌ 实时数据获取失败")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_tencent_api()
