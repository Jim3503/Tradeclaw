"""
Integration of Financial Memory System with Tradeclaw CrewAI agents.

This module provides enhanced agent classes that leverage the memory system
for improved decision-making and learning.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from crewai import Agent, Task

from .core import (
    FinancialMemoryStore,
    MemoryScope,
    AgentRole,
    MemoryLevel,
    MarketRegime,
    TimeHorizon
)


class MemoryEnhancedAgent:
    """
    Base class for memory-enhanced agents.

    Provides automatic memory integration for CrewAI agents.
    """

    def __init__(
        self,
        memory_dir: Optional[Path] = None,
        auto_save: bool = True
    ):
        """
        Initialize memory-enhanced agent.

        Args:
            memory_dir: Directory to load/save memory from/to
            auto_save: Whether to automatically save memory after updates
        """
        self.memory_dir = memory_dir or Path("memory")
        self.auto_save = auto_save

        # Load or create memory store
        self.memory = self._load_memory()

        # Initialize with default policies if new
        self._initialize_default_policies()

    def _load_memory(self) -> FinancialMemoryStore:
        """Load memory from disk or create new"""
        try:
            return FinancialMemoryStore(
                policy_file=self.memory_dir / "policies.json",
                episodic_file=self.memory_dir / "episodes.json",
                reflection_file=self.memory_dir / "reflections.pkl"
            )
        except Exception:
            return FinancialMemoryStore()

    def _initialize_default_policies(self):
        """Initialize with default trading policies if memory is empty"""
        if not self.memory.policy.get_policies():
            default_policies = [
                "Focus on risk management - never risk more than 2% on single trade",
                "Use technical indicators as confirmation, not sole signals",
                "Consider market regime when making trading decisions",
                "Always have clear exit strategy before entering position",
                "Learn from past trades - track outcomes and effectiveness"
            ]

            for policy in default_policies:
                self.memory.policy.add_policy(policy)

            if self.auto_save:
                self._save_memory()

    def _save_memory(self):
        """Save memory to disk"""
        try:
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            self.memory.save(self.memory_dir)
        except Exception as e:
            print(f"Warning: Failed to save memory: {e}")

    def enhance_task_description(
        self,
        base_description: str,
        agent_role: AgentRole,
        market_context: str
    ) -> str:
        """
        Enhance task description with relevant memory.

        Args:
            base_description: Original task description
            agent_role: Role of the agent
            market_context: Current market context

        Returns:
            Enhanced task description with memory
        """
        # Infer scope from market context
        scope = self._infer_scope_from_context(market_context)

        # Get relevant memory context
        memory_context = self.memory.to_prompt_context(
            agent_role=agent_role,
            query=market_context,
            scope=scope,
            top_k=3
        )

        # Combine with original description
        enhanced = f"""{base_description}

## Relevant Past Experience
{memory_context}

Use this past experience to inform your analysis and recommendations.
"""

        return enhanced

    def store_trading_experience(
        self,
        agent_role: AgentRole,
        situation: str,
        recommendation: str,
        rationale: str,
        confidence: MemoryLevel = MemoryLevel.MEDIUM,
        scope: Optional[MemoryScope] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store a trading experience in memory.

        Args:
            agent_role: Role of the agent
            situation: Description of the situation
            recommendation: What was recommended
            rationale: Reasoning behind recommendation
            confidence: Confidence level
            scope: Optional scope
            tags: Optional tags

        Returns:
            Entry ID
        """
        if scope is None:
            scope = MemoryScope()

        entry_id = self.memory.add_situation(
            situation=situation,
            recommendation=recommendation,
            rationale=rationale,
            confidence=confidence,
            scope=scope,
            source_agent=agent_role,
            tags=tags or []
        )

        if self.auto_save:
            self._save_memory()

        return entry_id

    def _infer_scope_from_context(self, context: str) -> MemoryScope:
        """
        Infer scope from market context text.

        Simple keyword matching to determine relevant scope.
        """
        scope = MemoryScope()

        # Sector keywords
        sector_keywords = {
            "Technology": ["tech", "software", "AI", "semiconductor", "chip"],
            "Healthcare": ["health", "medical", "pharma", "biotech"],
            "Finance": ["bank", "financial", "insurance", "fintech"],
            "Energy": ["oil", "gas", "energy", "solar"],
            "Consumer": ["retail", "consumer", "ecommerce"],
        }

        context_lower = context.lower()
        for sector, keywords in sector_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                scope.sectors.add(sector)

        # Market regime keywords
        if any(word in context_lower for word in ["rally", "bull", "uptrend"]):
            scope.market_regimes.add(MarketRegime.BULL_MARKET)
            scope.market_regimes.add(MarketRegime.RISK_ON)

        if any(word in context_lower for word in ["decline", "bear", "downtrend"]):
            scope.market_regimes.add(MarketRegime.BEAR_MARKET)
            scope.market_regimes.add(MarketRegime.RISK_OFF)

        # Time horizon keywords
        if any(word in context_lower for word in ["intraday", "day", "today"]):
            scope.time_horizons.add(TimeHorizon.DAY_TRADING)

        if any(word in context_lower for word in ["swing", "week", "short-term"]):
            scope.time_horizons.add(TimeHorizon.SWING_TRADING)

        return scope


class MemoryEnhancedTechnicalAgent:
    """
    Memory-enhanced technical analysis agent.

    Learns from past technical analysis and outcomes.
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_agent = MemoryEnhancedAgent(memory_dir)
        self.role = AgentRole.TECHNICAL_ANALYST

    def analyze_with_memory(
        self,
        stock_data: Dict[str, Any],
        market_context: str
    ) -> str:
        """
        Analyze stocks with memory-enhanced context.

        Args:
            stock_data: Stock technical data
            market_context: Market context description

        Returns:
            Analysis with memory-informed recommendations
        """
        # Get memory-enhanced analysis prompt
        enhanced_context = self.memory_agent.enhance_task_description(
            base_description="Analyze the technical indicators and provide trading recommendations.",
            agent_role=self.role,
            query=market_context
        )

        # Build full analysis prompt
        analysis_prompt = f"""
{enhanced_context}

## Current Stock Data
{stock_data}

## Current Market Context
{market_context}

Please provide:
1. Technical analysis (trends, support/resistance, indicators)
2. Trading recommendations (buy/sell/hold)
3. Risk management considerations
4. Key levels to watch
"""

        return analysis_prompt

    def store_analysis_result(
        self,
        situation: str,
        recommendation: str,
        technical_indicators: List[str]
    ) -> str:
        """Store technical analysis result in memory"""
        scope = MemoryScope()
        scope.time_horizons.add(TimeHorizon.SWING_TRADING)

        return self.memory_agent.store_trading_experience(
            agent_role=self.role,
            situation=situation,
            recommendation=recommendation,
            rationale=f"Technical analysis based on: {', '.join(technical_indicators)}",
            confidence=MemoryLevel.MEDIUM,
            scope=scope,
            tags=technical_indicators
        )


class MemoryEnhancedNarrativeAgent:
    """
    Memory-enhanced narrative analysis agent.

    Learns from past market narratives and their outcomes.
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_agent = MemoryEnhancedAgent(memory_dir)
        self.role = AgentRole.NARRATIVE_ANALYST

    def analyze_narrative_with_memory(
        self,
        news_data: Dict[str, Any],
        market_context: str
    ) -> str:
        """Analyze market narratives with memory"""
        enhanced_context = self.memory_agent.enhance_task_description(
            base_description="Analyze market narratives and identify key themes.",
            agent_role=self.role,
            query=market_context
        )

        analysis_prompt = f"""
{enhanced_context}

## Current News Data
{news_data}

## Market Context
{market_context}

Please identify:
1. Key market narratives and themes
2. Sentiment analysis (bullish/bearish/neutral)
3. Sector-specific narratives
4. Potential market-moving catalysts
"""

        return analysis_prompt

    def store_narrative_insight(
        self,
        narrative: str,
        recommendation: str,
        sectors: List[str]
    ) -> str:
        """Store narrative analysis in memory"""
        scope = MemoryScope()
        for sector in sectors:
            scope.sectors.add(sector)

        return self.memory_agent.store_trading_experience(
            agent_role=self.role,
            situation=narrative,
            recommendation=recommendation,
            rationale=f"Narrative analysis across sectors: {', '.join(sectors)}",
            confidence=MemoryLevel.MEDIUM,
            scope=scope,
            tags=["narrative"] + sectors
        )


class MemoryEnhancedPortfolioManager:
    """
    Memory-enhanced portfolio management agent.

    Learns from past portfolio decisions and outcomes.
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        self.memory_agent = MemoryEnhancedAgent(memory_dir)
        self.role = AgentRole.PORTFOLIO_MANAGER

    def make_decision_with_memory(
        self,
        current_holdings: List[Dict[str, Any]],
        market_analysis: str,
        technical_analysis: str
    ) -> str:
        """Make portfolio decisions with memory"""
        enhanced_context = self.memory_agent.enhance_task_description(
            base_description="Make portfolio management decisions.",
            agent_role=self.role,
            query=f"Portfolio decision context: {market_analysis}"
        )

        decision_prompt = f"""
{enhanced_context}

## Current Holdings
{current_holdings}

## Market Analysis
{market_analysis}

## Technical Analysis
{technical_analysis}

Please provide:
1. Portfolio rebalancing recommendations
2. Position sizing advice
3. Risk assessment
4. Specific actions (buy/sell/hold) for each position
"""

        return decision_prompt

    def store_portfolio_decision(
        self,
        situation: str,
        decision: str,
        rationale: str,
        effectiveness: Optional[float] = None
    ) -> str:
        """Store portfolio decision in memory"""
        scope = MemoryScope()
        scope.time_horizons.add(TimeHorizon.SWING_TRADING)

        return self.memory_agent.store_trading_experience(
            agent_role=self.role,
            situation=situation,
            recommendation=decision,
            rationale=rationale,
            confidence=MemoryLevel.HIGH,
            scope=scope,
            tags=["portfolio", "risk-management"]
        )


def create_memory_enhanced_crew(
    memory_dir: Optional[Path] = None,
    agents: Optional[List[Agent]] = None
) -> Dict[str, MemoryEnhancedAgent]:
    """
    Create memory-enhanced versions of all crew agents.

    Args:
        memory_dir: Directory for memory storage
        agents: Optional list of CrewAI agents to enhance

    Returns:
        Dictionary of memory-enhanced agents
    """
    memory_dir = memory_dir or Path("memory")

    enhanced_agents = {
        'technical': MemoryEnhancedTechnicalAgent(memory_dir),
        'narrative': MemoryEnhancedNarrativeAgent(memory_dir),
        'portfolio': MemoryEnhancedPortfolioManager(memory_dir),
    }

    return enhanced_agents


# Example usage function
def example_memory_integration():
    """
    Example of how to integrate memory with Tradeclaw crew.
    """
    # Initialize memory-enhanced agents
    enhanced_agents = create_memory_enhanced_crew(
        memory_dir=Path("memory")
    )

    # Example: Technical analysis with memory
    technical_agent = enhanced_agents['technical']

    stock_data = {
        'symbol': 'AAPL',
        'price': 175.50,
        'ma50': 172.30,
        'ma200': 168.90,
        'rsi': 58.2,
        'volume': '52M'
    }

    market_context = "Tech stocks rallying, AAPL breaking above MA50"

    # Get memory-enhanced analysis
    analysis_prompt = technical_agent.analyze_with_memory(
        stock_data=stock_data,
        market_context=market_context
    )

    print("Memory-Enhanced Analysis Prompt:")
    print(analysis_prompt)

    # After getting recommendation, store in memory
    recommendation = "Buy AAPL at $175.50, stop loss at $172, target $185"

    entry_id = technical_agent.store_analysis_result(
        situation=f"AAPL at ${stock_data['price']}, MA50 cross above",
        recommendation=recommendation,
        technical_indicators=["MA50", "MA200", "RSI"]
    )

    print(f"\nStored analysis with ID: {entry_id}")

    # Get memory stats
    stats = technical_agent.memory_agent.memory.get_stats()
    print(f"\nMemory Stats: {stats}")


if __name__ == "__main__":
    example_memory_integration()
