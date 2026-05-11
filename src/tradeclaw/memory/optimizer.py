"""
记忆优化模块 - 处理记忆效果追踪、自动提升和清理
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .core import (
    FinancialMemoryStore,
    MemoryEntry,
    MemoryLevel,
    MemoryScope,
    AgentRole
)


class MemoryOptimizer:
    """
    记忆优化器 - 自动管理记忆质量

    功能：
    1. 效果追踪：记录记忆的使用效果
    2. 自动提升：高质量记忆提升到反思层
    3. 智能去重：检测和合并重复记忆
    4. 定期清理：淘汰低质量记忆
    """

    def __init__(self, memory_store: FinancialMemoryStore):
        """
        初始化记忆优化器

        Args:
            memory_store: 要优化的记忆存储实例
        """
        self.memory_store = memory_store
        self.effectiveness_history: Dict[str, List[float]] = defaultdict(list)

    def track_effectiveness(
        self,
        entry_id: str,
        effectiveness: float,
        outcome: Optional[str] = None
    ) -> bool:
        """
        追踪记忆的效果评分

        Args:
            entry_id: 记忆条目ID
            effectiveness: 效果评分 (0.0 - 1.0)
            outcome: 实际结果描述（可选）

        Returns:
            是否成功更新
        """
        # 更新历史记录
        self.effectiveness_history[entry_id].append(effectiveness)

        # 计算平均效果
        avg_effectiveness = sum(self.effectiveness_history[entry_id]) / len(self.effectiveness_history[entry_id])

        # 更新记忆条目
        for entry in self.memory_store.episodic.entries:
            if entry.id == entry_id:
                entry.effectiveness = avg_effectiveness
                entry.outcome = outcome
                entry.verified = avg_effectiveness >= 0.7
                break

        # 如果效果足够好，自动提升到反思记忆
        if avg_effectiveness >= 0.7:
            self._promote_to_reflection(entry_id)

        return True

    def _promote_to_reflection(self, entry_id: str) -> bool:
        """
        将高质量记忆提升到反思层

        Args:
            entry_id: 要提升的记忆条目ID

        Returns:
            是否成功提升
        """
        # 找到对应的记忆条目
        target_entry = None
        for entry in self.memory_store.episodic.entries:
            if entry.id == entry_id:
                target_entry = entry
                break

        if not target_entry:
            return False

        # 标记为已验证
        target_entry.verified = True

        # 尝试添加到反思记忆
        success = self.memory_store.reflection.add_pattern(target_entry)

        if success:
            print(f"   ⭐ 记忆已提升到反思层: {target_entry.situation[:50]}...")

        return success

    def find_duplicates(
        self,
        similarity_threshold: float = 0.85
    ) -> List[Tuple[str, str, float]]:
        """
        查找重复的记忆

        Args:
            similarity_threshold: 相似度阈值（0-1）

        Returns:
            重复记忆对的列表 [(id1, id2, similarity), ...]
        """
        duplicates = []
        entries = self.memory_store.episodic.entries

        for i, entry1 in enumerate(entries):
            for j, entry2 in enumerate(entries[i+1:], i+1):
                similarity = self._compute_similarity(entry1, entry2)

                if similarity >= similarity_threshold:
                    duplicates.append((entry1.id, entry2.id, similarity))

        return duplicates

    def _compute_similarity(self, entry1: MemoryEntry, entry2: MemoryEntry) -> float:
        """
        计算两个记忆条目的相似度

        简单实现：基于文本相似度
        可以扩展为使用 embedding 相似度
        """
        # 检查完全相同的场景和建议
        if entry1.situation == entry2.situation and entry1.recommendation == entry2.recommendation:
            return 1.0

        # 简单的文本相似度（基于词汇重叠）
        words1 = set(entry1.situation.lower().split())
        words2 = set(entry2.situation.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def merge_duplicates(self, duplicates: List[Tuple[str, str, float]]) -> int:
        """
        合并重复的记忆

        Args:
            duplicates: 重复记忆对列表

        Returns:
            合并的记忆数量
        """
        merged_count = 0

        for id1, id2, similarity in duplicates:
            # 找到两个条目
            entry1 = None
            entry2 = None

            for entry in self.memory_store.episodic.entries:
                if entry.id == id1:
                    entry1 = entry
                elif entry.id == id2:
                    entry2 = entry

                if entry1 and entry2:
                    break

            if not entry1 or not entry2:
                continue

            # 保留效果更好的那个
            if entry2.effectiveness and (not entry1.effectiveness or entry2.effectiveness > entry1.effectiveness):
                entry1, entry2 = entry2, entry1

            # 合并信息
            if entry2.effectiveness and entry1.effectiveness:
                # 取平均效果
                entry1.effectiveness = (entry1.effectiveness + entry2.effectiveness) / 2
            elif entry2.effectiveness:
                entry1.effectiveness = entry2.effectiveness

            # 删除 entry2
            self.memory_store.episodic.entries.remove(entry2)
            merged_count += 1
            print(f"   🔗 合并重复记忆: {entry1.situation[:50]}...")

        return merged_count

    def cleanup_low_quality_memories(
        self,
        min_effectiveness: float = 0.3,
        max_age_days: int = 90
    ) -> int:
        """
        清理低质量记忆

        Args:
            min_effectiveness: 最低效果阈值
            max_age_days: 记忆最大保留天数

        Returns:
            清理的记忆数量
        """
        cleanup_count = 0
        now = datetime.now()
        cutoff_date = now - timedelta(days=max_age_days)

        entries_to_remove = []

        for entry in self.memory_store.episodic.entries:
            # 检查年龄
            entry_date = datetime.fromisoformat(entry.timestamp)
            if entry_date < cutoff_date:
                # 如果效果好，保留；否则删除
                if not entry.effectiveness or entry.effectiveness < min_effectiveness:
                    entries_to_remove.append(entry)
                    cleanup_count += 1

        # 删除低质量记忆
        for entry in entries_to_remove:
            self.memory_store.episodic.entries.remove(entry)
            print(f"   🗑️  清理低质量记忆: {entry.situation[:50]}...")

        return cleanup_count

    def optimize_all(
        self,
        enable_promotion: bool = True,
        enable_dedup: bool = True,
        enable_cleanup: bool = False,  # 默认关闭自动清理
        cleanup_threshold: float = 0.3,
        cleanup_max_age: int = 90
    ) -> Dict[str, int]:
        """
        执行所有优化操作

        Args:
            enable_promotion: 是否启用自动提升
            enable_dedup: 是否启用去重
            enable_cleanup: 是否启用清理
            cleanup_threshold: 清理阈值
            cleanup_max_age: 清理最大天数

        Returns:
            优化结果统计
        """
        print("\n🔧 开始记忆优化...")
        results = {
            'promoted': 0,
            'merged': 0,
            'cleaned': 0
        }

        # 1. 自动提升高质量记忆
        if enable_promotion:
            print("\n1️⃣ 自动提升高质量记忆...")
            promoted_count = 0
            for entry in self.memory_store.episodic.entries:
                if entry.effectiveness and entry.effectiveness >= 0.7 and not entry.verified:
                    if self._promote_to_reflection(entry.id):
                        promoted_count += 1
            results['promoted'] = promoted_count

        # 2. 去重
        if enable_dedup:
            print("\n2️⃣ 查找和合并重复记忆...")
            duplicates = self.find_duplicates(similarity_threshold=0.85)
            if duplicates:
                print(f"   发现 {len(duplicates)} 对重复记忆")
                results['merged'] = self.merge_duplicates(duplicates)
            else:
                print("   ✅ 未发现重复记忆")

        # 3. 清理低质量记忆
        if enable_cleanup:
            print("\n3️⃣ 清理低质量记忆...")
            results['cleaned'] = self.cleanup_low_quality_memories(
                min_effectiveness=cleanup_threshold,
                max_age_days=cleanup_max_age
            )

        print("\n✅ 记忆优化完成")
        print(f"   提升: {results['promoted']} 条")
        print(f"   合并: {results['merged']} 条")
        print(f"   清理: {results['cleaned']} 条")

        return results

    def get_memory_stats(self) -> Dict[str, any]:
        """获取记忆系统统计信息"""
        stats = self.memory_store.get_stats()

        # 额外统计
        verified_count = sum(1 for e in self.memory_store.episodic.entries if e.verified)
        with_effectiveness = sum(1 for e in self.memory_store.episodic.entries if e.effectiveness)

        avg_effectiveness = 0.0
        if with_effectiveness > 0:
            total_effectiveness = sum(e.effectiveness for e in self.memory_store.episodic.entries if e.effectiveness)
            avg_effectiveness = total_effectiveness / with_effectiveness

        stats.update({
            'verified_count': verified_count,
            'with_effectiveness': with_effectiveness,
            'avg_effectiveness': avg_effectiveness
        })

        return stats


def create_memory_optimizer(memory_store: FinancialMemoryStore) -> MemoryOptimizer:
    """
    创建记忆优化器实例

    Args:
        memory_store: 记忆存储实例

    Returns:
        MemoryOptimizer 实例
    """
    return MemoryOptimizer(memory_store)
