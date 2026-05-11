"""
分析记录保存系统
- 保存每次分析的完整记录
- 支持多维度检索
- 从历史中学习
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re


class AnalysisHistory:
    """分析历史记录管理器"""

    def __init__(self, history_dir: str = "memory/analysis_history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.history_dir / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """加载历史索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_index(self):
        """保存历史索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)

    def save_analysis(
        self,
        date: str,
        market_data: Dict,
        holdings_analysis: Dict,
        technical_signals: Dict,
        hot_sectors: List[str],
        recommendations: str,
        tags: List[str] = None
    ):
        """
        保存分析记录

        Args:
            date: 分析日期
            market_data: 市场数据（指数、涨跌等）
            holdings_analysis: 持仓分析
            technical_signals: 技术信号
            hot_sectors: 热点板块
            recommendations: 操作建议
            tags: 标签
        """
        record_id = f"analysis_{date}"

        record = {
            'date': date,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'market_data': market_data,
            'holdings_analysis': holdings_analysis,
            'technical_signals': technical_signals,
            'hot_sectors': hot_sectors,
            'recommendations': recommendations,
            'tags': tags or [],
            'market_phase': self._detect_market_phase(market_data, technical_signals),
            'performance_summary': self._summarize_performance(holdings_analysis)
        }

        # 保存完整记录
        record_file = self.history_dir / f"{record_id}.json"
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        # 更新索引
        self.index[record_id] = {
            'date': date,
            'timestamp': record['timestamp'],
            'market_phase': record['market_phase'],
            'tags': record['tags'],
            'hot_sectors': hot_sectors[:3],  # 保存前3个热点板块
            'file': str(record_file)
        }
        self._save_index()

        print(f"✅ 分析记录已保存: {record_id}")

    def _detect_market_phase(self, market_data: Dict, signals: Dict) -> str:
        """判断市场阶段"""
        # 简单判断逻辑
        sh_change = market_data.get('上证指数', {}).get('change', 0)
        trend = signals.get('overall_trend', 'unknown')

        if sh_change > 1 and trend == 'up':
            return '强势上涨'
        elif sh_change > 0 and trend == 'up':
            return '温和上涨'
        elif sh_change < -1:
            return '调整'
        elif abs(sh_change) < 0.5:
            return '震荡'
        else:
            return '过渡期'

    def _summarize_performance(self, holdings: Dict) -> Dict:
        """汇总持仓表现"""
        profitable = 0
        loss = 0
        total_profit = 0

        for stock_id, analysis in holdings.items():
            change_pct = analysis.get('change_pct', 0)
            if change_pct > 0:
                profitable += 1
                total_profit += change_pct
            else:
                loss += 1

        return {
            'profitable_count': profitable,
            'loss_count': loss,
            'win_rate': profitable / (profitable + loss) if (profitable + loss) > 0 else 0,
            'avg_profit': total_profit / profitable if profitable > 0 else 0
        }

    def search_by_market_phase(self, phase: str, limit: int = 5) -> List[Dict]:
        """根据市场阶段搜索历史记录"""
        results = []
        for record_id, info in self.index.items():
            if phase.lower() in info['market_phase'].lower():
                results.append({
                    'record_id': record_id,
                    'date': info['date'],
                    'market_phase': info['market_phase'],
                    'file': info['file']
                })

        # 按日期排序
        results.sort(key=lambda x: x['date'], reverse=True)
        return results[:limit]

    def search_by_hot_sector(self, sector: str, limit: int = 5) -> List[Dict]:
        """根据热点板块搜索历史记录"""
        results = []
        for record_id, info in self.index.items():
            for hot_sector in info['hot_sectors']:
                if sector.lower() in hot_sector.lower():
                    results.append({
                        'record_id': record_id,
                        'date': info['date'],
                        'hot_sector': hot_sector,
                        'file': info['file']
                    })
                    break

        results.sort(key=lambda x: x['date'], reverse=True)
        return results[:limit]

    def get_similar_market(self, market_data: Dict, limit: int = 3) -> List[Dict]:
        """
        查找相似市场环境的历史记录

        Args:
            market_data: 当前市场数据
            limit: 返回数量

        Returns:
            相似的历史记录列表
        """
        results = []
        sh_change = market_data.get('上证指数', {}).get('change', 0)

        # 查找涨跌幅相近的记录
        for record_id, info in self.index.items():
            # 读取完整记录获取具体涨跌幅
            record_file = Path(info['file'])
            if record_file.exists():
                with open(record_file, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                    record_sh_change = record['market_data'].get('上证指数', {}).get('change', 0)

                    # 相似度判断：涨跌幅差异小于1%
                    if abs(record_sh_change - sh_change) < 1.0:
                        results.append({
                            'record_id': record_id,
                            'date': info['date'],
                            'similarity': 1 - abs(record_sh_change - sh_change),
                            'market_phase': info['market_phase'],
                            'recommendations': record.get('recommendations', ''),
                            'file': info['file']
                        })

        # 按相似度排序
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]

    def get_record(self, record_id: str) -> Optional[Dict]:
        """获取完整的分析记录"""
        if record_id in self.index:
            record_file = Path(self.index[record_id]['file'])
            if record_file.exists():
                with open(record_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None

    def get_recent_records(self, limit: int = 10) -> List[Dict]:
        """获取最近的分析记录"""
        records = []
        for record_id, info in sorted(
            self.index.items(),
            key=lambda x: x[1]['date'],
            reverse=True
        )[:limit]:
            record = self.get_record(record_id)
            if record:
                records.append(record)
        return records


# 全局实例
_analysis_history = None

def get_analysis_history() -> AnalysisHistory:
    """获取全局分析历史实例"""
    global _analysis_history
    if _analysis_history is None:
        _analysis_history = AnalysisHistory()
    return _analysis_history


if __name__ == "__main__":
    # 测试功能
    history = AnalysisHistory()

    print("测试分析历史系统")
    print("=" * 60)

    # 测试保存
    test_market_data = {
        '上证指数': {'close': 3200, 'change': 0.5},
        '深证成指': {'close': 11500, 'change': 1.2}
    }

    test_holdings = {
        '600150': {'change_pct': 2.5, 'trend': 'up'},
        '513310': {'change_pct': -1.2, 'trend': 'down'}
    }

    history.save_analysis(
        date="2026-05-07",
        market_data=test_market_data,
        holdings_analysis=test_holdings,
        technical_signals={'overall_trend': 'up'},
        hot_sectors=["半导体", "AI"],
        recommendations="持有待涨",
        tags=["上涨", "科技"]
    )

    # 测试搜索
    print("\n测试搜索功能:")
    similar = history.get_similar_market(test_market_data)
    print(f"相似记录: {len(similar)} 条")

    # 测试获取记录
    print("\n测试获取记录:")
    record = history.get_record("analysis_2026-05-07")
    if record:
        print(f"✅ 获取成功: {record['date']}")
        print(f"   市场阶段: {record['market_phase']}")
        print(f"   热点板块: {record['hot_sectors']}")
