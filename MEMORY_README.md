# Financial Memory System for Tradeclaw

A sophisticated three-layer RAG (Retrieval-Augmented Generation) memory system designed for AI trading agents, inspired by Claude Code's memory architecture and Anthropic's contextual retrieval best practices.

## Features

### 🧠 Three-Layer Memory Architecture

1. **Policy Memory** - Long-term trading rules and principles
   - Stable, session-independent knowledge
   - Benefits from prompt caching
   - Always loaded for context

2. **Episodic Memory** - Historical trading situations with rich context
   - BM25-based retrieval with scope filtering
   - Outcome tracking and effectiveness scoring
   - Rich metadata for intelligent filtering

3. **Reflection Memory** - Validated patterns from cross-session learning
   - Only high-effectiveness, verified patterns
   - Automatic promotion from episodic memory
   - Continuously validated and updated

### 🎯 Key Capabilities

- **Smart Retrieval**: Hybrid BM25 + embedding search with scope-based filtering and rank fusion
- **Semantic Search**: Sentence-transformers based semantic similarity for concept matching
- **Write Governance**: Confidence filtering, duplicate detection, effectiveness tracking
- **Scope-Based Filtering**: Filter by agent role, sector, market regime, time horizon
- **Prompt Optimization**: Structured output for efficient LLM consumption
- **Persistence**: Full save/load support with automatic backups

## Quick Start

### Installation

```bash
# Install dependencies
pip install rank-bm25 sentence-transformers numpy

# The memory system is included with Tradeclaw
pip install -e .
```

### Basic Usage

```python
from tradeclaw.memory import (
    FinancialMemoryStore,
    MemoryScope,
    AgentRole,
    MemoryLevel,
    MarketRegime
)

# Initialize memory store
memory = FinancialMemoryStore()

# Add trading policies
memory.policy.add_policy("Never risk more than 2% on single trade")
memory.policy.add_policy("Always use stop-loss orders")

# Store trading situations
scope = MemoryScope()
scope.sectors.add("Technology")
scope.market_regimes.add(MarketRegime.RISK_OFF)

memory.add_situation(
    situation="High inflation + rising rates, tech stocks weak",
    recommendation="Reduce tech exposure, increase defensive positions",
    rationale="Rising rates depress growth valuations",
    confidence=MemoryLevel.HIGH,
    scope=scope,
    source_agent=AgentRole.PORTFOLIO_MANAGER,
    outcome="Tech fell 8%, defensive rose 3%",
    effectiveness=0.85
)

# Retrieve relevant memories
results = memory.retrieve_for_agent(
    agent_role=AgentRole.TRADER,
    query="Tech stocks in risk-off environment",
    scope=scope,
    top_k=3
)

# Advanced: Hybrid retrieval with custom alpha
from tradeclaw.memory.core import EpisodicFinancialMemory

# Enable embeddings for semantic search
episodic_memory = EpisodicFinancialMemory(
    enable_embeddings=True,
    embedding_model="all-MiniLM-L6-v2"  # Fast, good quality model
)

# Retrieve with hybrid search
results = episodic_memory.retrieve(
    query="software companies performing well",  # Semantic query
    scope=scope,
    top_k=5,
    use_hybrid=True,  # Use hybrid BM25 + embeddings
    alpha=0.5  # 0.0 = BM25 only, 1.0 = embeddings only, 0.5 = balanced
)

# Generate prompt context for LLM
prompt_context = memory.to_prompt_context(
    agent_role=AgentRole.TRADER,
    query="What to do with tech positions?",
    scope=scope
)

# Save to disk
memory.save(Path("memory"))
```

## Documentation

- **[Quick Start Guide](MEMORY_GUIDE.md)** - Get started quickly with examples
- **[Architecture Documentation](MEMORY_ARCHITECTURE.md)** - Deep dive into system design
- **[API Reference](#api-reference)** - Complete API documentation
- **[Examples](examples/)** - Practical code examples

## Architecture

### Memory Flow

```
Agent Action → Write Governance → Episodic Memory
                                          ↓
                                    Effectiveness Check
                                          ↓
                                    (if >= 0.7)
                                          ↓
                                Reflection Memory
```

### Retrieval Flow

```
Agent Query → Scope Inference → Policy Memory (always)
                          ↓
                  Reflection Memory (validated)
                          ↓
                  Hybrid Retrieval (BM25 + Embeddings)
                          ↓
                  Rank Fusion (alpha-weighted)
                          ↓
                  Scope Filtering
                          ↓
                  Prompt Context
```

### Hybrid Search Algorithm

The memory system uses **Hybrid BM25 + Embedding Retrieval** with configurable rank fusion:

1. **BM25 (Keyword Search)**: Finds exact keyword matches
2. **Semantic Search**: Uses sentence-transformers for concept matching
3. **Rank Fusion**: Combines scores using weighted average:
   - `final_score = alpha * embedding_score + (1 - alpha) * bm25_score`
   - Default `alpha = 0.5` for balanced retrieval
   - Adjust `alpha` based on your use case:
     - `alpha = 0.0`: Pure keyword search (BM25 only)
     - `alpha = 0.5`: Balanced hybrid search
     - `alpha = 1.0`: Pure semantic search (embeddings only)

**Benefits:**
- **Keyword matching** ensures exact term relevance
- **Semantic search** finds conceptually similar memories even with different words
- **Scope filtering** boosts results matching agent role, sector, market regime
- **Graceful degradation** falls back to BM25 if embeddings unavailable

## Integration with Tradeclaw

The memory system integrates seamlessly with your existing Tradeclaw agents:

```python
from tradeclaw.memory.integration import MemoryEnhancedTechnicalAgent

# Create memory-enhanced agent
agent = MemoryEnhancedTechnicalAgent(memory_dir=Path("memory"))

# Analyze with memory context
analysis_prompt = agent.analyze_with_memory(
    stock_data=stock_data,
    market_context=market_context
)

# Store experience for future learning
agent.store_analysis_result(
    situation="AAPL breaking above MA50",
    recommendation="Go long with 2% risk",
    technical_indicators=["MA50", "RSI", "Volume"]
)
```

## API Reference

### FinancialMemoryStore

Main orchestrator for the memory system.

**Methods:**
- `add_situation()` - Add new trading situation
- `retrieve_for_agent()` - Retrieve relevant memories for agent
- `to_prompt_context()` - Generate optimized prompt context
- `save()` - Save all memories to disk
- `get_stats()` - Get memory statistics

### MemoryScope

Defines context for memory filtering and retrieval.

**Attributes:**
- `agent_roles` - Which agents can access
- `tickers` - Specific stock symbols
- `sectors` - Market sectors
- `market_regimes` - Market conditions (RISK_ON, RISK_OFF, etc.)
- `time_horizons` - Trading timeframes

### MemoryEntry

Core data structure for individual memories.

**Fields:**
- `situation` - Description of the situation
- `recommendation` - What was recommended
- `rationale` - Reasoning behind recommendation
- `confidence` - Confidence level (LOW/MEDIUM/HIGH)
- `scope` - Context scope
- `outcome` - What actually happened
- `effectiveness` - How effective (0.0 to 1.0)

## Examples

### Example 1: Basic Memory Usage

```python
from tradeclaw.memory import FinancialMemoryStore, MemoryScope, AgentRole

memory = FinancialMemoryStore()

# Add a trading rule
memory.policy.add_policy("Always respect stop losses")

# Store a trading situation
scope = MemoryScope()
scope.sectors.add("Technology")

memory.add_situation(
    situation="Tech stocks breaking out with volume",
    recommendation="Increase tech exposure",
    rationale="Strong momentum confirmed",
    confidence=MemoryLevel.HIGH,
    scope=scope,
    source_agent=AgentRole.TRADER
)
```

### Example 2: Retrieving Relevant Memories

```python
# Define query scope
query_scope = MemoryScope()
query_scope.sectors.add("Technology")

# Retrieve relevant memories
results = memory.retrieve_for_agent(
    agent_role=AgentRole.TRADER,
    query="What to do with tech breakout?",
    scope=query_scope,
    top_k=3
)

# Process results
for result in results:
    entry = result['entry']
    score = result['score']
    print(f"Score: {score:.2f}")
    print(f"Recommendation: {entry.recommendation}")
```

### Example 3: Generating Prompt Context

```python
# Get memory context for LLM
prompt_context = memory.to_prompt_context(
    agent_role=AgentRole.TRADER,
    query="Tech breakout trading",
    scope=query_scope,
    top_k=3
)

# Use in prompt
full_prompt = f"""
{prompt_context}

Current Situation: Tech stocks breaking out
What action should I take?
"""
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest tests/test_memory.py -v

# Run specific test
python -m pytest tests/test_memory.py::TestFinancialMemoryStore -v

# Run with coverage
python -m pytest tests/test_memory.py --cov=tradeclaw/memory
```

## Performance Considerations

- **Storage**: O(n) where n = number of memories
- **Retrieval**: O(n) for BM25, optimized with indexing
- **Memory Usage**: ~1KB per memory entry
- **Prompt Overhead**: ~50-200 tokens per retrieved memory

## Best Practices

### 1. Writing Effective Memories

```python
# ✅ Good: Specific and actionable
memory.add_situation(
    situation="NVDA earnings beat, guidance raised 20%, stock down 5% on macro concerns",
    recommendation="Buy dip if holds above $400 support",
    rationale="Strong fundamentals vs temporary macro fear",
    confidence=MemoryLevel.HIGH,
    scope=scope,
    source_agent=AgentRole.TRADER
)

# ❌ Bad: Too vague
memory.add_situation(
    situation="Stocks moving",
    recommendation="Do something",
    rationale="Analysis",
    confidence=MemoryLevel.LOW,
    scope=scope,
    source_agent=AgentRole.TRADER
)
```

### 2. Using Scopes Effectively

```python
# ✅ Good: Specific scope
tech_scope = MemoryScope()
tech_scope.sectors.add("Technology")
tech_scope.market_regimes.add(MarketRegime.EARNINGS_SEASON)

# ❌ Bad: Empty scope (matches everything)
vague_scope = MemoryScope()
```

### 3. Tracking Outcomes

```python
# Store initial decision
entry_id = memory.add_situation(
    situation="AAPL breaking above MA50",
    recommendation="Go long",
    rationale="Technical breakout",
    confidence=MemoryLevel.HIGH,
    scope=scope,
    source_agent=AgentRole.TRADER
)

# Update with outcome later
for entry in memory.episodic.entries:
    if entry.id == entry_id:
        entry.outcome = "Trade gained +3.2% in 2 days"
        entry.effectiveness = 0.85
        entry.verified = True
        break
```

## Troubleshooting

### Issue: BM25 not working

```bash
pip install rank-bm25
```

### Issue: No memories retrieved

```python
# Try without scope first
results = memory.retrieve_for_agent(
    agent_role=AgentRole.TRADER,
    query="your query",
    scope=None,  # No scope filter
    top_k=10
)
```

## Advanced Usage

### Hybrid Retrieval Configuration

```python
from tradeclaw.memory import EpisodicFinancialMemory

# Configure memory with custom embedding model
memory = EpisodicFinancialMemory(
    enable_embeddings=True,
    embedding_model="all-mpnet-base-v2"  # Higher quality, slower
)

# Retrieval strategies for different scenarios:

# 1. Exact keyword matching (e.g., ticker symbols, specific terms)
results = memory.retrieve(query="AAPL breakout", use_hybrid=False, alpha=0.0)

# 2. Semantic concept matching (e.g., "software companies" → "IT sector")
results = memory.retrieve(query="software companies doing well", use_hybrid=True, alpha=0.7)

# 3. Balanced approach (default)
results = memory.retrieve(query="tech stocks", use_hybrid=True, alpha=0.5)

# 4. Embeddings-only (best for conceptual queries)
results = memory.retrieve(query="technology sector performance", use_hybrid=True, alpha=1.0)
```

### When to Use Different Alpha Values

- **alpha = 0.0 (BM25 only)**:
  - Searching for specific tickers, technical indicators
  - Exact phrase matching needed
  - Fastest retrieval speed

- **alpha = 0.3-0.5 (BM25-biased)**:
  - General trading situations
  - Mix of specific terms and concepts
  - Balanced performance

- **alpha = 0.7-1.0 (Embedding-biased)**:
  - Conceptual queries ("growth strategies", "risk management")
  - Finding similar situations with different terminology
  - Cross-domain pattern matching

### Performance Optimization

```python
# Disable embeddings for faster, keyword-only search
memory = EpisodicFinancialMemory(enable_embeddings=False)

# Use smaller model for faster encoding
memory = EpisodicFinancialMemory(
    enable_embeddings=True,
    embedding_model="all-MiniLM-L6-v2"  # Fast: ~50ms per encode
)

# Use larger model for better quality
memory = EpisodicFinancialMemory(
    enable_embeddings=True,
    embedding_model="all-mpnet-base-v2"  # Slower: ~200ms per encode
)
```

### Issue: Too many irrelevant memories

```python
# Increase thresholds
results = memory.retrieve_for_agent(
    agent_role=AgentRole.TRADER,
    query="your query",
    scope=scope,
    top_k=3,  # Fewer results
    min_score=0.6  # Higher threshold
)
```

## Contributing

When extending the memory system:

1. Maintain the three-layer separation
2. Always add metadata to new memory types
3. Implement scope filtering for new retrieval methods
4. Add write governance for new memory additions
5. Update prompt context generation for new memory types
6. Add tests for new functionality

## License

This project is part of Tradeclaw and follows the same license.

## Acknowledgments

- Inspired by [Claude Code's memory architecture](https://docs.claude.com/en/docs/claude-code)
- Based on [Anthropic's contextual retrieval research](https://www.anthropic.com/research/contextual-retrieval)
- Built with [rank-bm25](https://github.com/dorianbrown/rank_bm25) for efficient retrieval

## Support

For issues, questions, or contributions, please visit the [Tradeclaw repository](https://github.com/yourusername/tradeclaw).

---

**Version**: 2.0.0
**Last Updated**: 2026-04-01
**Status**: Production Ready ✅
