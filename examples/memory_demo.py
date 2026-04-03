"""
Quick demonstration of the Financial Memory System.

This script shows how to:
1. Initialize the memory store
2. Add trading policies
3. Store trading situations
4. Retrieve relevant memories
5. Generate prompt context
"""

from pathlib import Path
from tradeclaw.memory import (
    FinancialMemoryStore,
    MemoryScope,
    AgentRole,
    MemoryLevel,
    MarketRegime,
    TimeHorizon
)


def main():
    print("=== Financial Memory System Demo ===\n")

    # 1. Initialize memory store
    print("1. Initializing memory store...")
    memory = FinancialMemoryStore()
    print("   ✓ Memory store created\n")

    # 2. Add trading policies
    print("2. Adding trading policies...")
    policies = [
        "Never risk more than 2% of portfolio on a single trade",
        "Always use stop-loss orders to limit downside",
        "Focus on high-conviction ideas with strong catalysts",
        "Maintain diversified exposure across sectors"
    ]

    for policy in policies:
        memory.policy.add_policy(policy)

    print(f"   ✓ Added {len(policies)} policies\n")

    # 3. Store trading situations
    print("3. Storing trading situations...")

    # Situation 1: Tech sector in risk-off environment
    tech_scope = MemoryScope()
    tech_scope.sectors.add("Technology")
    tech_scope.market_regimes.add(MarketRegime.RISK_OFF)
    tech_scope.time_horizons.add(TimeHorizon.SWING_TRADING)

    memory.add_situation(
        situation="High inflation concerns + rising interest rates, technology stocks showing weakness",
        recommendation="Reduce technology exposure, increase defensive positions (utilities, consumer staples)",
        rationale="Rising interest rates depress growth stock valuations; defensive sectors outperform in risk-off environments",
        confidence=MemoryLevel.HIGH,
        scope=tech_scope,
        source_agent=AgentRole.PORTFOLIO_MANAGER,
        outcome="Tech sector fell 8%, defensive sectors rose 3% - avoided significant losses",
        effectiveness=0.85,
        tags=["inflation", "rates", "sector_rotation", "risk_off"],
        market_conditions="CPI at 4.2%, Fed funds rate at 5.25%, market volatility elevated"
    )
    print("   ✓ Stored: Tech sector risk-off situation")

    # Situation 2: Earnings season trading
    earnings_scope = MemoryScope()
    earnings_scope.market_regimes.add(MarketRegime.EARNINGS_SEASON)
    earnings_scope.time_horizons.add(TimeHorizon.DAY_TRADING)

    memory.add_situation(
        situation="NVDA earnings beat expectations by 20%, guidance raised 15%, but stock down 5% pre-market on macro concerns",
        recommendation="Buy the dip if stock holds above $400 support level with tight stop loss",
        rationale="Strong fundamentals and guidance vs temporary macro fear; earnings beat creates positive setup",
        confidence=MemoryLevel.HIGH,
        scope=earnings_scope,
        source_agent=AgentRole.TRADER,
        outcome="Stock bounced off $402, rallied to $445 (+10.8%) in 3 days",
        effectiveness=0.92,
        tags=["earnings", "dip_buying", "NVDA", "support_level"],
        market_conditions="Earnings season, market concerns about Fed policy, NVDA reporting Q3"
    )
    print("   ✓ Stored: Earnings season dip-buying situation")

    # Situation 3: Market regime change
    regime_scope = MemoryScope()
    regime_scope.market_regimes.add(MarketRegime.RISK_ON)
    regime_scope.time_horizons.add(TimeHorizon.SWING_TRADING)

    memory.add_situation(
        situation="Fed signals dovish pivot, market breadth expanding, small caps leading",
        recommendation="Increase risk exposure, add small-cap and growth positions, reduce defensive holdings",
        rationale="Dovish Fed typically benefits risk assets; market breadth improvement confirms regime change to risk-on",
        confidence=MemoryLevel.MEDIUM,
        scope=regime_scope,
        source_agent=AgentRole.PORTFOLIO_MANAGER,
        outcome="Portfolio increased exposure, small caps gained 15% over next month",
        effectiveness=0.78,
        tags=["fed", "regime_change", "risk_on", "small_caps"],
        market_conditions="Fed minutes show pivot concerns, market breadth expanding from 40% to 65%"
    )
    print("   ✓ Stored: Market regime change situation")

    print(f"   ✓ Total situations stored: {len(memory.episodic.entries)}\n")

    # 4. Retrieve relevant memories
    print("4. Retrieving relevant memories...")

    query_scope = MemoryScope()
    query_scope.sectors.add("Technology")
    query_scope.market_regimes.add(MarketRegime.RISK_OFF)

    results = memory.retrieve_for_agent(
        agent_role=AgentRole.PORTFOLIO_MANAGER,
        query="Technology stocks facing rising rates and inflation concerns",
        scope=query_scope,
        top_k=3
    )

    print(f"   ✓ Found {len(results)} relevant memories\n")

    # Display retrieved memories
    for i, result in enumerate(results, 1):
        entry = result['entry']
        score = result['score']
        print(f"   Memory {i} (Relevance: {score:.1%})")
        print(f"   ┌─ Situation: {entry.situation[:80]}...")
        print(f"   ├─ Recommendation: {entry.recommendation[:80]}...")
        print(f"   ├─ Effectiveness: {entry.effectiveness:.1%}" if entry.effectiveness else "   ├─ Effectiveness: Not yet tracked")
        print(f"   └─ Source: {entry.source_agent.name}\n")

    # 5. Generate prompt context
    print("5. Generating prompt context for LLM...")
    prompt_context = memory.to_prompt_context(
        agent_role=AgentRole.PORTFOLIO_MANAGER,
        query="Tech stocks in risk-off environment with rising rates",
        scope=query_scope,
        top_k=2
    )

    print("   ✓ Prompt context generated:\n")
    print("   " + "="*60)
    print(prompt_context[:500] + "...")
    print("   " + "="*60 + "\n")

    # 6. Show statistics
    print("6. Memory statistics:")
    stats = memory.get_stats()
    print(f"   ├─ Policies: {stats['policy_count']}")
    print(f"   ├─ Episodic memories: {stats['episodic_count']}")
    print(f"   ├─ Reflection patterns: {stats['reflection_count']}")
    print(f"   └─ Total memories: {stats['total_memories']}\n")

    # 7. Save to disk
    print("7. Saving memory to disk...")
    memory.save(Path("memory"))
    print("   ✓ Memory saved to 'memory/' directory\n")

    print("=== Demo Complete ===")
    print("\nNext steps:")
    print("• Integrate with your Tradeclaw agents")
    print("• Track outcomes and update effectiveness")
    print("• Add more trading situations")
    print("• Experiment with different scope configurations")


if __name__ == "__main__":
    main()
