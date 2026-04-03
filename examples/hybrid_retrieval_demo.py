#!/usr/bin/env python3
"""
Demonstration of Hybrid BM25 + Embedding Retrieval in Tradeclaw Memory System.

This script shows how the hybrid retrieval system combines keyword-based BM25
search with semantic embedding search for comprehensive memory retrieval.
"""

from tradeclaw.memory.core import (
    EpisodicFinancialMemory,
    MemoryScope,
    MemoryLevel,
    AgentRole,
    MarketRegime,
    MemoryEntry
)
from datetime import datetime


def create_sample_memory():
    """Create a sample memory with various trading situations."""
    memory = EpisodicFinancialMemory(
        enable_embeddings=True,
        embedding_model="all-MiniLM-L6-v2"
    )

    # Sample trading situations with varied terminology
    situations = [
        {
            "situation": "Technology stocks rallying strongly with high volume",
            "recommendation": "Increase exposure to tech sector",
            "rationale": "Strong momentum and positive sentiment in technology",
            "sector": "Technology"
        },
        {
            "situation": "IT companies showing significant growth momentum",
            "recommendation": "Buy more software and hardware stocks",
            "rationale": "Information technology sector experiencing rapid expansion",
            "sector": "Technology"
        },
        {
            "situation": "Healthcare stocks declining due to regulatory concerns",
            "recommendation": "Reduce healthcare positions",
            "rationale": "New regulations negatively impacting medical companies",
            "sector": "Healthcare"
        },
        {
            "situation": "Bank stocks rising with interest rate hikes",
            "recommendation": "Invest in financial sector",
            "rationale": "Higher interest rates benefit financial institutions",
            "sector": "Financial"
        },
        {
            "situation": "Energy companies surging on oil price increase",
            "recommendation": "Add energy exposure",
            "rationale": "Rising oil prices boost energy sector profitability",
            "sector": "Energy"
        }
    ]

    # Add situations to memory
    for i, situation_data in enumerate(situations):
        scope = MemoryScope()
        scope.sectors.add(situation_data["sector"])

        entry = MemoryEntry(
            id="",
            situation=situation_data["situation"],
            recommendation=situation_data["recommendation"],
            rationale=situation_data["rationale"],
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )
        memory.add_entry(entry)
        print(f"Added: {situation_data['situation'][:50]}...")

    return memory


def demonstrate_hybrid_retrieval(memory):
    """Demonstrate different retrieval strategies."""
    print("\n" + "="*80)
    print("HYBRID RETRIEVAL DEMONSTRATION")
    print("="*80)

    # Query with semantically similar but different keywords
    query = "software companies performing well"
    print(f"\nQuery: '{query}'")
    print("-" * 80)

    # 1. BM25 only (keyword-based)
    print("\n1. BM25 Only (Keyword-based Search):")
    print("   Best for: Exact keyword matches, ticker symbols")
    results_bm25 = memory.retrieve(
        query=query,
        use_hybrid=False,
        top_k=3
    )
    for i, result in enumerate(results_bm25, 1):
        entry = result['entry']
        print(f"   {i}. [{result['score']:.2f}] {entry.situation[:60]}...")

    # 2. Hybrid with alpha=0.3 (BM25-biased)
    print("\n2. Hybrid Search (Alpha=0.3, BM25-biased):")
    print("   Best for: General trading situations, mix of terms and concepts")
    results_hybrid_03 = memory.retrieve(
        query=query,
        use_hybrid=True,
        alpha=0.3,
        top_k=3
    )
    for i, result in enumerate(results_hybrid_03, 1):
        entry = result['entry']
        print(f"   {i}. [{result['score']:.2f}] {entry.situation[:60]}...")

    # 3. Hybrid with alpha=0.5 (balanced)
    print("\n3. Hybrid Search (Alpha=0.5, Balanced):")
    print("   Best for: Most use cases, default balanced approach")
    results_hybrid_05 = memory.retrieve(
        query=query,
        use_hybrid=True,
        alpha=0.5,
        top_k=3
    )
    for i, result in enumerate(results_hybrid_05, 1):
        entry = result['entry']
        print(f"   {i}. [{result['score']:.2f}] {entry.situation[:60]}...")

    # 4. Hybrid with alpha=0.7 (embedding-biased)
    print("\n4. Hybrid Search (Alpha=0.7, Embedding-biased):")
    print("   Best for: Conceptual queries, cross-domain pattern matching")
    results_hybrid_07 = memory.retrieve(
        query=query,
        use_hybrid=True,
        alpha=0.7,
        top_k=3
    )
    for i, result in enumerate(results_hybrid_07, 1):
        entry = result['entry']
        print(f"   {i}. [{result['score']:.2f}] {entry.situation[:60]}...")

    # 5. Embeddings only
    print("\n5. Embeddings Only (Pure Semantic Search):")
    print("   Best for: Finding conceptually similar situations with different words")
    results_embedding = memory.retrieve(
        query=query,
        use_hybrid=True,
        alpha=1.0,
        top_k=3
    )
    for i, result in enumerate(results_embedding, 1):
        entry = result['entry']
        print(f"   {i}. [{result['score']:.2f}] {entry.situation[:60]}...")


def demonstrate_scope_filtering(memory):
    """Demonstrate scope-based filtering with hybrid retrieval."""
    print("\n" + "="*80)
    print("SCOPE FILTERING WITH HYBRID RETRIEVAL")
    print("="*80)

    query = "stocks with good momentum"
    print(f"\nQuery: '{query}'")

    # Without scope filtering
    print("\n1. Without Scope Filtering:")
    print("   Returns: All matching memories regardless of sector")
    results_no_scope = memory.retrieve(
        query=query,
        use_hybrid=True,
        alpha=0.5,
        top_k=5
    )
    for i, result in enumerate(results_no_scope, 1):
        entry = result['entry']
        scope_sectors = ", ".join(entry.scope.sectors) if entry.scope.sectors else "Any"
        print(f"   {i}. [{result['score']:.2f}] [{scope_sectors}] {entry.situation[:50]}...")

    # With Technology scope
    print("\n2. With Technology Scope Filter:")
    print("   Returns: Prioritizes technology-related memories")
    tech_scope = MemoryScope()
    tech_scope.sectors.add("Technology")
    results_tech = memory.retrieve(
        query=query,
        scope=tech_scope,
        use_hybrid=True,
        alpha=0.5,
        top_k=5
    )
    for i, result in enumerate(results_tech, 1):
        entry = result['entry']
        scope_sectors = ", ".join(entry.scope.sectors) if entry.scope.sectors else "Any"
        print(f"   {i}. [{result['score']:.2f}] [{scope_sectors}] {entry.situation[:50]}...")


def demonstrate_semantic_matching():
    """Demonstrate semantic matching capabilities."""
    print("\n" + "="*80)
    print("SEMANTIC MATCHING DEMONSTRATION")
    print("="*80)

    memory = EpisodicFinancialMemory(enable_embeddings=True)

    # Add situation with specific terminology
    scope = MemoryScope()
    scope.sectors.add("Technology")

    entry = MemoryEntry(
        id="",
        situation="Technology stocks breaking out above resistance levels",
        recommendation="Go long on tech stocks",
        rationale="Strong momentum and volume confirmation",
        confidence=MemoryLevel.HIGH,
        scope=scope,
        timestamp=datetime.now().isoformat(),
        source_agent=AgentRole.TRADER
    )
    memory.add_entry(entry)

    print("\nStored Situation: 'Technology stocks breaking out above resistance levels'")

    # Query with different but semantically similar terms
    queries = [
        "software companies rallying",
        "IT sector gaining ground",
        "tech shares moving upward"
    ]

    print("\nSemantic Matches (using different terminology):")
    for query in queries:
        results = memory.retrieve(
            query=query,
            use_hybrid=True,
            alpha=0.7,  # Embedding-biased for semantic matching
            top_k=1
        )
        if results:
            score = results[0]['score']
            print(f"  Query: '{query}' → Match Score: {score:.2f}")


def main():
    """Run all demonstrations."""
    print("Tradeclaw Hybrid Retrieval Demonstration")
    print("="*80)

    # Create sample memory
    print("\nCreating sample memory with trading situations...")
    memory = create_sample_memory()

    # Demonstrate hybrid retrieval
    demonstrate_hybrid_retrieval(memory)

    # Demonstrate scope filtering
    demonstrate_scope_filtering(memory)

    # Demonstrate semantic matching
    demonstrate_semantic_matching()

    print("\n" + "="*80)
    print("Demonstration complete!")
    print("="*80)
    print("\nKey Takeaways:")
    print("• BM25 is best for exact keyword matches (e.g., ticker symbols)")
    print("• Embeddings find conceptually similar situations with different words")
    print("• Hybrid search (alpha=0.5) provides balanced retrieval for most cases")
    print("• Adjust alpha based on your use case:")
    print("  - alpha=0.0: Pure keyword search")
    print("  - alpha=0.5: Balanced hybrid search")
    print("  - alpha=1.0: Pure semantic search")
    print("• Scope filtering boosts results matching agent role, sector, etc.")


if __name__ == "__main__":
    main()
