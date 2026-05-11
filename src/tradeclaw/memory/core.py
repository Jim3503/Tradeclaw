"""
Core memory system implementation for Tradeclaw financial memory system.

This module implements the three-layer memory architecture:
- PolicyMemory: Long-term trading rules
- EpisodicFinancialMemory: Historical situations with BM25 retrieval
- ReflectionMemory: Validated patterns from cross-session learning
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import hashlib

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("Warning: rank_bm25 not available. Install with: pip install rank-bm25")

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False
    np = None
    print("Warning: sentence-transformers not available. Install with: pip install sentence-transformers")


class MemoryLevel(Enum):
    """Confidence level for memory entries"""
    LOW = 1      # Tentative, goes to temp buffer
    MEDIUM = 2   # Moderate confidence
    HIGH = 3     # High confidence, verified


class AgentRole(Enum):
    """Different agent roles in the trading system"""
    DATA_FETCHER = auto()
    NARRATIVE_ANALYST = auto()
    TECHNICAL_ANALYST = auto()
    SENTIMENT_ANALYST = auto()
    PORTFOLIO_MANAGER = auto()
    RISK_MANAGER = auto()
    REPORT_COMPILER = auto()
    TRADER = auto()


class MarketRegime(Enum):
    """Different market regimes for context filtering"""
    RISK_ON = auto()        # Risk appetite high, growth stocks outperform
    RISK_OFF = auto()       # Risk appetite low, defensive stocks outperform
    BULL_MARKET = auto()    # General uptrend
    BEAR_MARKET = auto()    # General downtrend
    SIDEWAYS = auto()       # Range-bound market
    EARNINGS_SEASON = auto()  # During earnings reports
    VOLATILE = auto()       # High volatility period


class TimeHorizon(Enum):
    """Time horizon for trading decisions"""
    SCALPING = auto()       # Seconds to minutes
    DAY_TRADING = auto()    # Intraday
    SWING_TRADING = auto()  # Days to weeks
    POSITION_TRADING = auto()  # Weeks to months
    LONG_TERM_INVESTING = auto()  # Months to years


@dataclass
class MemoryScope:
    """
    Defines the scope/context for memory filtering and retrieval.

    This allows agents to only retrieve memories relevant to:
    - Their role (trader vs analyst vs risk_manager)
    - Specific assets (tickers, sectors)
    - Market conditions (regimes)
    - Time horizons (short vs long term)
    """
    agent_roles: Set[AgentRole] = field(default_factory=set)
    tickers: Set[str] = field(default_factory=set)
    sectors: Set[str] = field(default_factory=set)
    market_regimes: Set[MarketRegime] = field(default_factory=set)
    time_horizons: Set[TimeHorizon] = field(default_factory=set)

    def matches(self, other_scope: 'MemoryScope') -> float:
        """
        Calculate how well this scope matches another scope.
        Returns a score between 0.0 (no match) and 1.0 (perfect match).
        """
        if not other_scope:
            return 0.5  # Neutral score if no scope specified

        matches = []

        # Check each dimension
        if self.agent_roles and other_scope.agent_roles:
            role_match = len(self.agent_roles & other_scope.agent_roles) / max(len(self.agent_roles), 1)
            matches.append(role_match)

        if self.tickers and other_scope.tickers:
            ticker_match = len(self.tickers & other_scope.tickers) / max(len(self.tickers), 1)
            matches.append(ticker_match)

        if self.sectors and other_scope.sectors:
            sector_match = len(self.sectors & other_scope.sectors) / max(len(self.sectors), 1)
            matches.append(sector_match)

        if self.market_regimes and other_scope.market_regimes:
            regime_match = len(self.market_regimes & other_scope.market_regimes) / max(len(self.market_regimes), 1)
            matches.append(regime_match)

        if self.time_horizons and other_scope.time_horizons:
            horizon_match = len(self.time_horizons & other_scope.time_horizons) / max(len(self.time_horizons), 1)
            matches.append(horizon_match)

        return sum(matches) / len(matches) if matches else 0.5

    def to_dict(self) -> Dict[str, List[str]]:
        """Convert to dictionary for JSON serialization"""
        return {
            'agent_roles': [r.name for r in self.agent_roles],
            'tickers': list(self.tickers),
            'sectors': list(self.sectors),
            'market_regimes': [r.name for r in self.market_regimes],
            'time_horizons': [h.name for h in self.time_horizons]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, List[str]]) -> 'MemoryScope':
        """Create from dictionary"""
        scope = cls()

        if 'agent_roles' in data:
            scope.agent_roles = {AgentRole[r] for r in data['agent_roles']}

        if 'tickers' in data:
            scope.tickers = set(data['tickers'])

        if 'sectors' in data:
            scope.sectors = set(data['sectors'])

        if 'market_regimes' in data:
            scope.market_regimes = {MarketRegime[r] for r in data['market_regimes']}

        if 'time_horizons' in data:
            scope.time_horizons = {TimeHorizon[h] for h in data['time_horizons']}

        return scope


@dataclass
class MemoryEntry:
    """
    A single memory entry with rich metadata.

    Contains the situation, recommendation, outcome, and effectiveness tracking.
    """
    id: str
    situation: str
    recommendation: str
    rationale: str
    confidence: MemoryLevel
    scope: MemoryScope
    timestamp: str
    source_agent: AgentRole

    # Optional outcome tracking
    outcome: Optional[str] = None
    effectiveness: Optional[float] = None  # 0.0 to 1.0
    verified: bool = False

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    market_conditions: Optional[str] = None

    def __post_init__(self):
        """Generate ID if not provided"""
        if not self.id:
            content = f"{self.situation}:{self.recommendation}:{self.timestamp}"
            self.id = hashlib.md5(content.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'situation': self.situation,
            'recommendation': self.recommendation,
            'rationale': self.rationale,
            'confidence': self.confidence.name,
            'scope': self.scope.to_dict(),
            'timestamp': self.timestamp,
            'source_agent': self.source_agent.name,
            'outcome': self.outcome,
            'effectiveness': self.effectiveness,
            'verified': self.verified,
            'tags': self.tags,
            'market_conditions': self.market_conditions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        scope = MemoryScope.from_dict(data.get('scope', {}))

        return cls(
            id=data['id'],
            situation=data['situation'],
            recommendation=data['recommendation'],
            rationale=data['rationale'],
            confidence=MemoryLevel[data['confidence']],
            scope=scope,
            timestamp=data['timestamp'],
            source_agent=AgentRole[data['source_agent']],
            outcome=data.get('outcome'),
            effectiveness=data.get('effectiveness'),
            verified=data.get('verified', False),
            tags=data.get('tags', []),
            market_conditions=data.get('market_conditions')
        )


class PolicyMemory:
    """
    Policy Memory stores long-term trading rules and principles.

    Similar to Claude Code's CLAUDE.md - stable, session-independent rules
    that benefit from prompt caching.
    """

    def __init__(self):
        self.policies: List[str] = []

    def add_policy(self, policy: str) -> None:
        """Add a new policy"""
        if policy not in self.policies:
            self.policies.append(policy)

    def get_policies(self) -> List[str]:
        """Get all policies"""
        return self.policies.copy()

    def clear(self) -> None:
        """Clear all policies"""
        self.policies.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {'policies': self.policies}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolicyMemory':
        """Create from dictionary"""
        policy_memory = cls()
        policy_memory.policies = data.get('policies', [])
        return policy_memory


class EmbeddingEncoder:
    """
    Handles text encoding using sentence-transformers for semantic search.

    Provides caching and batch processing for efficient embedding generation.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding encoder.

        Args:
            model_name: Name of the sentence-transformers model to use
                       Default: all-MiniLM-L6-v2 (fast, good quality)
        """
        if not EMBEDDING_AVAILABLE:
            raise ImportError("sentence-transformers is required for embeddings. Install with: pip install sentence-transformers")

        self.model_name = model_name
        self.model = None
        self._embedding_cache = {}
        self._initialized = False

    def _initialize_model(self):
        """Lazy initialization of the model"""
        if not self._initialized:
            try:
                self.model = SentenceTransformer(self.model_name)
                self._initialized = True
            except Exception as e:
                print(f"Warning: Failed to load embedding model {self.model_name}: {e}")
                print("Falling back to BM25-only retrieval")
                self._initialized = False

    def encode(self, texts: Union[str, List[str]], show_progress: bool = False) -> 'np.ndarray':
        """
        Encode text(s) into embeddings.

        Args:
            texts: Single text or list of texts to encode
            show_progress: Whether to show progress bar for batch encoding

        Returns:
            numpy array of embeddings
        """
        self._initialize_model()

        if not self._initialized or self.model is None:
            # Return zero embeddings as fallback
            if isinstance(texts, str):
                return np.zeros(384)  # Default embedding size for MiniLM
            else:
                return np.zeros((len(texts), 384))

        # Check cache for single text
        if isinstance(texts, str):
            if texts in self._embedding_cache:
                return self._embedding_cache[texts]
            embedding = self.model.encode(texts)
            self._embedding_cache[texts] = embedding
            return embedding
        else:
            # Batch encoding
            return self.model.encode(texts)

    def compute_similarity(self, query_embedding: 'np.ndarray',
                         document_embeddings: 'np.ndarray') -> List[float]:
        """
        Compute cosine similarity between query and documents.

        Args:
            query_embedding: Query embedding vector
            document_embeddings: Document embedding matrix

        Returns:
            List of similarity scores
        """
        if not EMBEDDING_AVAILABLE:
            return [0.0] * len(document_embeddings)

        # Compute cosine similarity
        similarities = np.dot(document_embeddings, query_embedding) / (
            np.linalg.norm(document_embeddings, axis=1) * np.linalg.norm(query_embedding) + 1e-8
        )
        return similarities.tolist()

    def clear_cache(self):
        """Clear the embedding cache"""
        self._embedding_cache.clear()


class EpisodicFinancialMemory:
    """
    Episodic Memory stores historical trading situations with rich context.

    Implements hybrid BM25 + embedding retrieval with scope filtering and rank fusion.
    Supports both keyword-based and semantic search for comprehensive memory retrieval.
    """

    def __init__(self, enable_embeddings: bool = True, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the episodic memory.

        Args:
            enable_embeddings: Whether to enable semantic search with embeddings
            embedding_model: Name of the sentence-transformers model to use
        """
        self.entries: List[MemoryEntry] = []
        self._bm25_index: Optional['BM25Okapi'] = None
        self._tokenized_entries: List[List[str]] = []
        self._index_dirty = True

        # Embedding support
        self.enable_embeddings = enable_embeddings and EMBEDDING_AVAILABLE
        self.embedding_encoder: Optional[EmbeddingEncoder] = None
        self._embeddings: Optional['np.ndarray'] = None
        self._embedding_index_dirty = True

        if self.enable_embeddings:
            try:
                self.embedding_encoder = EmbeddingEncoder(model_name=embedding_model)
            except Exception as e:
                print(f"Warning: Could not initialize embedding encoder: {e}")
                print("Falling back to BM25-only retrieval")
                self.enable_embeddings = False

    def add_entry(self, entry: MemoryEntry) -> bool:
        """
        Add a new entry with duplicate detection.

        Returns True if added, False if duplicate detected.
        """
        # Check for duplicates
        for existing in self.entries:
            if self._is_duplicate(entry, existing):
                return False

        self.entries.append(entry)
        self._index_dirty = True
        self._embedding_index_dirty = True
        return True

    def _is_duplicate(self, entry1: MemoryEntry, entry2: MemoryEntry, threshold: float = 0.85) -> bool:
        """Check if two entries are duplicates based on text similarity"""
        # Simple duplicate check: same situation and recommendation
        if entry1.situation == entry2.situation and entry1.recommendation == entry2.recommendation:
            return True

        # Could add more sophisticated duplicate detection here
        # e.g., using embeddings or text similarity metrics

        return False

    def retrieve(
        self,
        query: str,
        scope: Optional[MemoryScope] = None,
        top_k: int = 5,
        min_score: float = 0.0,
        use_hybrid: bool = True,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories using hybrid BM25 + embedding retrieval.

        Args:
            query: Search query
            scope: Optional scope filter
            top_k: Number of results to return
            min_score: Minimum relevance score (0.0 to 1.0)
            use_hybrid: Whether to use hybrid retrieval (True) or BM25 only (False)
            alpha: Weight for hybrid retrieval (0.0 = BM25 only, 1.0 = embeddings only, 0.5 = balanced)

        Returns:
            List of dictionaries containing entry data and relevance scores
        """
        if not self.entries:
            return []

        # Rebuild indices if needed
        if self._index_dirty:
            self._rebuild_index()

        if self._embedding_index_dirty and self.enable_embeddings:
            self._rebuild_embedding_index()

        # Get BM25 scores
        query_tokens = self._tokenize(query)
        if BM25_AVAILABLE and self._bm25_index:
            bm25_scores = self._bm25_index.get_scores(query_tokens)
        else:
            bm25_scores = self._fallback_scores(query_tokens)

        # Normalize BM25 scores to 0-1 range
        if bm25_scores is not None and len(bm25_scores) > 0:
            max_score = max(bm25_scores)
            min_score_val = min(bm25_scores)
            if max_score > min_score_val:
                bm25_normalized = [(s - min_score_val) / (max_score - min_score_val) for s in bm25_scores]
            else:
                bm25_normalized = [0.5] * len(bm25_scores)
        else:
            bm25_normalized = [0.0] * len(self.entries)

        # Get embedding scores if available and enabled
        if self.enable_embeddings and use_hybrid and self.embedding_encoder and self._embeddings is not None:
            query_embedding = self.embedding_encoder.encode(query)
            embedding_scores = self.embedding_encoder.compute_similarity(query_embedding, self._embeddings)

            # Normalize embedding scores to 0-1 range
            if embedding_scores is not None and len(embedding_scores) > 0:
                max_score = max(embedding_scores)
                min_score_val = min(embedding_scores)
                if max_score > min_score_val:
                    embedding_normalized = [(s - min_score_val) / (max_score - min_score_val) for s in embedding_scores]
                else:
                    embedding_normalized = [0.5] * len(embedding_scores)
            else:
                embedding_normalized = [0.0] * len(self.entries)

            # Hybrid rank fusion
            final_scores = [
                alpha * emb_score + (1 - alpha) * bm25_score
                for emb_score, bm25_score in zip(embedding_normalized, bm25_normalized)
            ]
        else:
            # BM25 only
            final_scores = bm25_normalized

        # Apply scope filtering and boost
        for i, entry in enumerate(self.entries):
            base_score = final_scores[i]

            # Apply scope filtering
            if scope:
                scope_match = entry.scope.matches(scope)
                # Boost by scope match
                final_score = base_score * (0.5 + 0.5 * scope_match)

                # Apply hard filter if scope is very specific
                if scope_match < 0.2:
                    final_score = 0.0
            else:
                final_score = base_score

            final_scores[i] = final_score

        # Sort by score and filter
        indexed_scores = list(enumerate(final_scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score >= min_score:
                entry = self.entries[idx]
                results.append({
                    'entry': entry,
                    'score': score,
                    'relevance': score
                })

        return results

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Convert to lowercase and split on non-alphanumeric
        import re
        tokens = re.findall(r'\w+', text.lower())
        return tokens

    def _rebuild_index(self) -> None:
        """Rebuild the BM25 index"""
        if not BM25_AVAILABLE:
            return

        self._tokenized_entries = [self._tokenize(
            f"{entry.situation} {entry.recommendation} {entry.rationale}"
        ) for entry in self.entries]

        self._bm25_index = BM25Okapi(self._tokenized_entries)
        self._index_dirty = False

    def _rebuild_embedding_index(self) -> None:
        """Rebuild the embedding index"""
        if not self.enable_embeddings or self.embedding_encoder is None:
            return

        # Prepare texts for encoding
        texts = [
            f"{entry.situation} {entry.recommendation} {entry.rationale}"
            for entry in self.entries
        ]

        # Encode all entries
        try:
            self._embeddings = self.embedding_encoder.encode(texts)
            self._embedding_index_dirty = False
        except Exception as e:
            print(f"Warning: Failed to build embedding index: {e}")
            self.enable_embeddings = False
            self._embeddings = None

    def _fallback_scores(self, query_tokens: List[str]) -> List[float]:
        """Fallback scoring when BM25 is not available"""
        scores = []
        for entry in self.entries:
            entry_text = f"{entry.situation} {entry.recommendation}".lower()
            score = sum(1 for token in query_tokens if token in entry_text)
            scores.append(float(score))
        return scores

    def get_entries(self, scope: Optional[MemoryScope] = None) -> List[MemoryEntry]:
        """Get all entries, optionally filtered by scope"""
        if not scope:
            return self.entries.copy()

        filtered = []
        for entry in self.entries:
            if entry.scope.matches(scope) > 0.3:
                filtered.append(entry)

        return filtered

    def clear(self) -> None:
        """Clear all entries"""
        self.entries.clear()
        self._bm25_index = None
        self._tokenized_entries = []
        self._index_dirty = True
        self._embeddings = None
        self._embedding_index_dirty = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'entries': [entry.to_dict() for entry in self.entries]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EpisodicFinancialMemory':
        """Create from dictionary"""
        memory = cls()
        for entry_data in data.get('entries', []):
            entry = MemoryEntry.from_dict(entry_data)
            memory.entries.append(entry)
        memory._index_dirty = True
        return memory


class ReflectionMemory:
    """
    Reflection Memory stores validated patterns from cross-session learning.

    Only high-effectiveness, verified patterns make it here.
    Similar to Claude's auto-memory but with effectiveness gating.
    """

    def __init__(self):
        self.patterns: List[MemoryEntry] = []
        self._effectiveness_threshold = 0.7  # Only patterns with effectiveness >= 0.7

    def add_pattern(self, entry: MemoryEntry) -> bool:
        """
        Add a validated pattern.

        Only adds if:
        - Effectiveness >= threshold
        - Verified == True
        - Not duplicate
        """
        if not entry.verified:
            return False

        if entry.effectiveness is None or entry.effectiveness < self._effectiveness_threshold:
            return False

        # Check for duplicates
        for existing in self.patterns:
            if existing.situation == entry.situation and existing.recommendation == entry.recommendation:
                return False

        self.patterns.append(entry)
        return True

    def get_patterns(self, scope: Optional[MemoryScope] = None) -> List[MemoryEntry]:
        """Get validated patterns, optionally filtered by scope"""
        if not scope:
            return self.patterns.copy()

        filtered = []
        for pattern in self.patterns:
            if pattern.scope.matches(scope) > 0.3:
                filtered.append(pattern)

        return filtered

    def update_effectiveness(self, entry_id: str, new_effectiveness: float) -> bool:
        """Update effectiveness of a pattern"""
        for pattern in self.patterns:
            if pattern.id == entry_id:
                pattern.effectiveness = new_effectiveness

                # Remove if below threshold
                if new_effectiveness < self._effectiveness_threshold:
                    self.patterns.remove(pattern)

                return True
        return False

    def clear(self) -> None:
        """Clear all patterns"""
        self.patterns.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'patterns': [pattern.to_dict() for pattern in self.patterns],
            'effectiveness_threshold': self._effectiveness_threshold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReflectionMemory':
        """Create from dictionary"""
        memory = cls()
        memory._effectiveness_threshold = data.get('effectiveness_threshold', 0.7)

        for pattern_data in data.get('patterns', []):
            pattern = MemoryEntry.from_dict(pattern_data)
            memory.patterns.append(pattern)

        return memory


class FinancialMemoryStore:
    """
    Main orchestrator for the three-layer memory system.

    Combines Policy Memory, Episodic Memory, and Reflection Memory
    with intelligent retrieval and prompt optimization.
    """

    def __init__(
        self,
        policy_file: Optional[Path] = None,
        episodic_file: Optional[Path] = None,
        reflection_file: Optional[Path] = None
    ):
        """
        Initialize the memory store.

        Args:
            policy_file: Path to load/save policy memory
            episodic_file: Path to load/save episodic memory
            reflection_file: Path to load/save reflection memory
        """
        self.policy = PolicyMemory()
        self.episodic = EpisodicFinancialMemory()
        self.reflection = ReflectionMemory()

        # Load from files if provided
        if policy_file and policy_file.exists():
            self._load_policy(policy_file)

        if episodic_file and episodic_file.exists():
            self._load_episodic(episodic_file)

        if reflection_file and reflection_file.exists():
            self._load_reflection(reflection_file)

    def add_situation(
        self,
        situation: str,
        recommendation: str,
        rationale: str,
        confidence: MemoryLevel,
        scope: MemoryScope,
        source_agent: AgentRole,
        outcome: Optional[str] = None,
        effectiveness: Optional[float] = None,
        tags: List[str] = None,
        market_conditions: Optional[str] = None
    ) -> str:
        """
        Add a new situation to episodic memory.

        Args:
            situation: Description of the situation
            recommendation: What was recommended
            rationale: Reasoning for the recommendation
            confidence: Confidence level
            scope: Scope/context for filtering
            source_agent: Which agent created this memory
            outcome: What actually happened (optional)
            effectiveness: How effective the recommendation was (0.0 to 1.0)
            tags: Optional tags for categorization
            market_conditions: Optional market conditions description

        Returns:
            The ID of the created entry
        """
        # Create entry
        entry = MemoryEntry(
            id="",
            situation=situation,
            recommendation=recommendation,
            rationale=rationale,
            confidence=confidence,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=source_agent,
            outcome=outcome,
            effectiveness=effectiveness,
            tags=tags or [],
            market_conditions=market_conditions
        )

        # Add to episodic memory
        if self.episodic.add_entry(entry):
            # If high effectiveness and verified, also add to reflection
            if effectiveness and effectiveness >= 0.7:
                entry.verified = True
                self.reflection.add_pattern(entry)

        return entry.id

    def retrieve_for_agent(
        self,
        agent_role: AgentRole,
        query: str,
        scope: Optional[MemoryScope] = None,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories relevant to a specific agent.

        Args:
            agent_role: The role of the agent requesting memories
            query: Search query
            scope: Optional scope filter
            top_k: Number of results to return
            min_score: Minimum relevance score

        Returns:
            List of relevant memories with scores
        """
        # Add agent role to scope
        if scope is None:
            scope = MemoryScope()

        scope.agent_roles.add(agent_role)

        # Retrieve from episodic memory
        results = self.episodic.retrieve(
            query=query,
            scope=scope,
            top_k=top_k,
            min_score=min_score
        )

        return results

    def to_prompt_context(
        self,
        agent_role: AgentRole,
        query: str,
        scope: Optional[MemoryScope] = None,
        top_k: int = 3
    ) -> str:
        """
        Generate optimized prompt context with memory.

        Structure:
        1. Stable prefix (policies) - benefits from prompt caching
        2. Dynamic suffix (retrieved episodes) - based on query

        Args:
            agent_role: The role of the agent
            query: Search query
            scope: Optional scope filter
            top_k: Number of relevant episodes to include

        Returns:
            Formatted string for prompt injection
        """
        parts = []

        # 1. Policies (stable prefix)
        policies = self.policy.get_policies()
        if policies:
            parts.append("## Trading Policies and Principles\n")
            for i, policy in enumerate(policies, 1):
                parts.append(f"{i}. {policy}\n")
            parts.append("\n")

        # 2. Reflection patterns (validated learnings)
        if scope:
            patterns = self.reflection.get_patterns(scope)
        else:
            patterns = self.reflection.get_patterns()

        if patterns:
            parts.append("## Validated Trading Patterns\n")
            for i, pattern in enumerate(patterns[:3], 1):
                parts.append(f"### Pattern {i}\n")
                parts.append(f"Situation: {pattern.situation}\n")
                parts.append(f"Recommendation: {pattern.recommendation}\n")
                parts.append(f"Effectiveness: {pattern.effectiveness:.1%}\n")
                parts.append(f"Rationale: {pattern.rationale}\n\n")

        # 3. Relevant episodes (dynamic suffix)
        episodes = self.retrieve_for_agent(
            agent_role=agent_role,
            query=query,
            scope=scope,
            top_k=top_k
        )

        if episodes:
            parts.append("## Relevant Past Experiences\n")
            for i, result in enumerate(episodes, 1):
                entry = result['entry']
                score = result['score']
                parts.append(f"### Experience {i} (Relevance: {score:.1%})\n")
                parts.append(f"Situation: {entry.situation}\n")
                parts.append(f"Recommendation: {entry.recommendation}\n")
                if entry.outcome:
                    parts.append(f"Outcome: {entry.outcome}\n")
                if entry.effectiveness:
                    parts.append(f"Effectiveness: {entry.effectiveness:.1%}\n")
                parts.append(f"Rationale: {entry.rationale}\n\n")

        return "\n".join(parts)

    def save(
        self,
        directory: Path,
        prefix: str = ""
    ) -> None:
        """
        Save all memory layers to disk.

        Args:
            directory: Directory to save to
            prefix: Optional prefix for filenames
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        # Save policy memory
        policy_file = directory / f"{prefix}policies.json"
        with open(policy_file, 'w', encoding='utf-8') as f:
            json.dump(self.policy.to_dict(), f, indent=2, ensure_ascii=False)

        # Save episodic memory
        episodic_file = directory / f"{prefix}episodes.json"
        with open(episodic_file, 'w', encoding='utf-8') as f:
            json.dump(self.episodic.to_dict(), f, indent=2, ensure_ascii=False)

        # Save reflection memory
        reflection_file = directory / f"{prefix}reflections.pkl"
        with open(reflection_file, 'wb') as f:
            pickle.dump(self.reflection.to_dict(), f)

    def _load_policy(self, filepath: Path) -> None:
        """Load policy memory from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.policy = PolicyMemory.from_dict(data)

    def _load_episodic(self, filepath: Path) -> None:
        """Load episodic memory from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.episodic = EpisodicFinancialMemory.from_dict(data)

    def _load_reflection(self, filepath: Path) -> None:
        """Load reflection memory from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.reflection = ReflectionMemory.from_dict(data)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory store"""
        return {
            'policy_count': len(self.policy.policies),
            'episodic_count': len(self.episodic.entries),
            'reflection_count': len(self.reflection.patterns),
            'total_memories': len(self.policy.policies) + len(self.episodic.entries) + len(self.reflection.patterns)
        }


# Convenience functions for quick usage
def create_memory_store(
    policies: List[str] = None,
    load_dir: Optional[Path] = None
) -> FinancialMemoryStore:
    """
    Quick factory function to create a memory store.

    Args:
        policies: Optional list of initial policies
        load_dir: Optional directory to load memories from

    Returns:
        Configured FinancialMemoryStore
    """
    if load_dir:
        store = FinancialMemoryStore(
            policy_file=load_dir / "policies.json",
            episodic_file=load_dir / "episodes.json",
            reflection_file=load_dir / "reflections.pkl"
        )
    else:
        store = FinancialMemoryStore()

    # Add initial policies
    if policies:
        for policy in policies:
            store.policy.add_policy(policy)

    return store
