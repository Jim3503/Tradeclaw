"""
Financial Memory System for Tradeclaw

A modern RAG architecture inspired by Claude Code's memory design and
Anthropic's contextual retrieval best practices.

This module provides a three-layer memory system:
1. Policy Memory - Long-term trading rules and principles
2. Episodic Memory - Historical trading situations and outcomes
3. Reflection Memory - Validated patterns from cross-session learning
"""

from .core import (
    MemoryLevel,
    MemoryScope,
    MarketRegime,
    TimeHorizon,
    AgentRole,
    MemoryEntry,
    PolicyMemory,
    EpisodicFinancialMemory,
    ReflectionMemory,
    FinancialMemoryStore
)

__all__ = [
    'MemoryLevel',
    'MemoryScope',
    'MarketRegime',
    'TimeHorizon',
    'AgentRole',
    'MemoryEntry',
    'PolicyMemory',
    'EpisodicFinancialMemory',
    'ReflectionMemory',
    'FinancialMemoryStore'
]

__version__ = '1.0.0'
