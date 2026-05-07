"""
K线数据缓存管理系统
- 缓存每次获取的K线数据
- 增量更新：只拉取最新的数据
- 持久化存储
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class KlineCache:
    """K线数据缓存管理器"""

    def __init__(self, cache_dir: str = "memory/kline_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """加载缓存索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """保存缓存索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def get_cache_file(self, code: str) -> Path:
        """获取缓存文件路径"""
        # 使用代码作为文件名
        return self.cache_dir / f"{code}.json"

    def get_cached_kline(self, code: str) -> Optional[List[List]]:
        """
        从缓存获取K线数据

        Returns:
            K线数据列表，如果没有缓存则返回None
        """
        cache_file = self.get_cache_file(code)

        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📦 从缓存加载 {code} 的 {len(data['kline'])} 条K线数据")
                return data['kline']

        return None

    def save_kline(self, code: str, kline: List[List], data_source: str = "unknown"):
        """
        保存K线数据到缓存

        Args:
            code: 股票代码
            kline: K线数据列表
            data_source: 数据来源
        """
        cache_file = self.get_cache_file(code)

        # 保存数据
        data = {
            'code': code,
            'kline': kline,
            'data_source': data_source,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'kline_count': len(kline)
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 更新索引
        if kline:
            latest_date = kline[-1][0]
            self.index[code] = {
                'latest_date': latest_date,
                'count': len(kline),
                'last_update': data['last_update']
            }
            self._save_index()

        print(f"💾 已缓存 {code} 的 {len(kline)} 条K线数据")

    def get_latest_date(self, code: str) -> Optional[str]:
        """获取某个代码的最新K线日期"""
        if code in self.index:
            return self.index[code]['latest_date']
        return None

    def merge_kline(self, cached: List[List], new_kline: List[List]) -> List[List]:
        """
        合并缓存的K线和新的K线数据（去重）

        Args:
            cached: 缓存的K线数据
            new_kline: 新获取的K线数据

        Returns:
            合并后的K线数据
        """
        # 创建日期到K线的映射（去重）
        kline_dict = {}

        # 先添加旧数据
        for k in cached:
            kline_dict[k[0]] = k

        # 新数据覆盖旧数据（可能更准确）
        for k in new_kline:
            kline_dict[k[0]] = k

        # 按日期排序
        sorted_kline = sorted(kline_dict.values(), key=lambda x: x[0])

        added = len(sorted_kline) - len(cached)
        if added > 0:
            print(f"📈 增量更新: 新增 {added} 条K线数据")

        return sorted_kline

    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'total_codes': len(self.index),
            'total_klines': sum(item['count'] for item in self.index.values()),
            'last_update': max([item['last_update'] for item in self.index.values()]) if self.index else None
        }


# 全局缓存实例
_kline_cache = None

def get_kline_cache() -> KlineCache:
    """获取全局K线缓存实例"""
    global _kline_cache
    if _kline_cache is None:
        _kline_cache = KlineCache()
    return _kline_cache


if __name__ == "__main__":
    # 测试缓存功能
    cache = KlineCache()

    print("测试K线缓存系统")
    print("=" * 60)

    # 测试保存
    test_kline = [
        ["2026-05-01", "600150", 40.0, 41.0, 39.5, 40.5, 100000, 4050000],
        ["2026-05-02", "600150", 40.5, 41.5, 40.0, 41.0, 120000, 4920000],
        ["2026-05-03", "600150", 41.0, 42.0, 40.5, 41.5, 110000, 4565000],
    ]

    cache.save_kline("600150", test_kline, "test_source")

    # 测试读取
    cached = cache.get_cached_kline("600150")
    if cached:
        print(f"\n✅ 缓存读取成功: {len(cached)} 条数据")
        print(f"最新日期: {cached[-1][0]}")

    # 测试合并
    new_kline = [
        ["2026-05-04", "600150", 41.5, 42.5, 41.0, 42.0, 130000, 5460000],
        ["2026-05-05", "600150", 42.0, 43.0, 41.5, 42.5, 140000, 5950000],
    ]

    merged = cache.merge_kline(cached, new_kline)
    print(f"\n✅ 合并后: {len(merged)} 条数据")

    # 测试统计
    stats = cache.get_cache_stats()
    print(f"\n📊 缓存统计:")
    print(f"  代码数量: {stats['total_codes']}")
    print(f"  K线总数: {stats['total_klines']}")
    print(f"  最后更新: {stats['last_update']}")
