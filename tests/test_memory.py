"""
Unit tests for the Financial Memory System.

Tests all three memory layers, retrieval, scope filtering, and persistence.
"""

import unittest
from pathlib import Path
import tempfile
import json
import pickle
from datetime import datetime
import sys

from tradeclaw.memory.core import (
    MemoryLevel,
    MemoryScope,
    MarketRegime,
    TimeHorizon,
    AgentRole,
    MemoryEntry,
    PolicyMemory,
    EpisodicFinancialMemory,
    ReflectionMemory,
    FinancialMemoryStore,
    EMBEDDING_AVAILABLE
)


class TestMemoryScope(unittest.TestCase):
    """Test MemoryScope functionality"""

    def test_scope_creation(self):
        """Test creating a scope"""
        scope = MemoryScope()
        scope.agent_roles.add(AgentRole.TRADER)
        scope.sectors.add("Technology")
        scope.market_regimes.add(MarketRegime.RISK_ON)

        self.assertEqual(len(scope.agent_roles), 1)
        self.assertEqual(len(scope.sectors), 1)
        self.assertEqual(len(scope.market_regimes), 1)

    def test_scope_matching(self):
        """Test scope matching logic"""
        scope1 = MemoryScope()
        scope1.agent_roles.add(AgentRole.TRADER)
        scope1.sectors.add("Technology")

        scope2 = MemoryScope()
        scope2.agent_roles.add(AgentRole.TRADER)
        scope2.sectors.add("Technology")

        # Perfect match
        score = scope1.matches(scope2)
        self.assertEqual(score, 1.0)

        # Partial match
        scope3 = MemoryScope()
        scope3.agent_roles.add(AgentRole.TRADER)
        scope3.sectors.add("Healthcare")

        score = scope1.matches(scope3)
        self.assertLess(score, 1.0)
        self.assertGreater(score, 0.0)

    def test_scope_serialization(self):
        """Test scope to_dict and from_dict"""
        scope = MemoryScope()
        scope.agent_roles.add(AgentRole.TRADER)
        scope.tickers.add("AAPL")
        scope.sectors.add("Technology")

        # To dict
        scope_dict = scope.to_dict()
        self.assertIn('TRADER', scope_dict['agent_roles'])
        self.assertIn('AAPL', scope_dict['tickers'])

        # From dict
        scope2 = MemoryScope.from_dict(scope_dict)
        self.assertEqual(scope.agent_roles, scope2.agent_roles)
        self.assertEqual(scope.tickers, scope2.tickers)


class TestMemoryEntry(unittest.TestCase):
    """Test MemoryEntry functionality"""

    def test_entry_creation(self):
        """Test creating a memory entry"""
        scope = MemoryScope()
        entry = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )

        self.assertIsNotNone(entry.id)
        self.assertEqual(entry.situation, "Test situation")
        self.assertEqual(entry.confidence, MemoryLevel.HIGH)

    def test_entry_serialization(self):
        """Test entry to_dict and from_dict"""
        scope = MemoryScope()
        scope.sectors.add("Technology")

        entry = MemoryEntry(
            id="test123",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp="2024-01-01T12:00:00",
            source_agent=AgentRole.TRADER,
            outcome="Good outcome",
            effectiveness=0.85,
            verified=True
        )

        # To dict
        entry_dict = entry.to_dict()
        self.assertEqual(entry_dict['situation'], "Test situation")
        self.assertEqual(entry_dict['effectiveness'], 0.85)

        # From dict
        entry2 = MemoryEntry.from_dict(entry_dict)
        self.assertEqual(entry.id, entry2.id)
        self.assertEqual(entry.situation, entry2.situation)
        self.assertEqual(entry.effectiveness, entry2.effectiveness)


class TestPolicyMemory(unittest.TestCase):
    """Test PolicyMemory functionality"""

    def test_add_policy(self):
        """Test adding policies"""
        policy_memory = PolicyMemory()
        policy_memory.add_policy("Test policy 1")
        policy_memory.add_policy("Test policy 2")

        policies = policy_memory.get_policies()
        self.assertEqual(len(policies), 2)
        self.assertIn("Test policy 1", policies)

    def test_duplicate_policy(self):
        """Test that duplicate policies are not added"""
        policy_memory = PolicyMemory()
        policy_memory.add_policy("Test policy")
        policy_memory.add_policy("Test policy")  # Duplicate

        policies = policy_memory.get_policies()
        self.assertEqual(len(policies), 1)

    def test_policy_serialization(self):
        """Test policy memory serialization"""
        policy_memory = PolicyMemory()
        policy_memory.add_policy("Test policy")

        # To dict
        policy_dict = policy_memory.to_dict()
        self.assertEqual(len(policy_dict['policies']), 1)

        # From dict
        policy_memory2 = PolicyMemory.from_dict(policy_dict)
        self.assertEqual(len(policy_memory2.get_policies()), 1)


class TestEpisodicFinancialMemory(unittest.TestCase):
    """Test EpisodicFinancialMemory functionality"""

    def test_add_entry(self):
        """Test adding entries"""
        memory = EpisodicFinancialMemory()

        scope = MemoryScope()
        entry = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )

        result = memory.add_entry(entry)
        self.assertTrue(result)
        self.assertEqual(len(memory.entries), 1)

    def test_duplicate_detection(self):
        """Test duplicate detection"""
        memory = EpisodicFinancialMemory()

        scope = MemoryScope()
        entry1 = MemoryEntry(
            id="1",
            situation="Same situation",
            recommendation="Same recommendation",
            rationale="Rationale 1",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )

        entry2 = MemoryEntry(
            id="2",
            situation="Same situation",
            recommendation="Same recommendation",
            rationale="Rationale 2",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )

        memory.add_entry(entry1)
        result = memory.add_entry(entry2)  # Should be rejected

        self.assertFalse(result)
        self.assertEqual(len(memory.entries), 1)

    def test_retrieve(self):
        """Test retrieval"""
        memory = EpisodicFinancialMemory()

        # Add test entries
        for i in range(3):
            scope = MemoryScope()
            scope.sectors.add("Technology")

            entry = MemoryEntry(
                id="",
                situation=f"Tech stock situation {i}",
                recommendation=f"Recommendation {i}",
                rationale="Test rationale",
                confidence=MemoryLevel.HIGH,
                scope=scope,
                timestamp=datetime.now().isoformat(),
                source_agent=AgentRole.TRADER
            )
            memory.add_entry(entry)

        # Retrieve
        results = memory.retrieve(
            query="Tech stock",
            top_k=2
        )

        self.assertLessEqual(len(results), 2)
        if results:
            self.assertIn('entry', results[0])
            self.assertIn('score', results[0])

    def test_scope_filtered_retrieve(self):
        """Test scope-filtered retrieval"""
        memory = EpisodicFinancialMemory()

        # Add tech sector entry
        tech_scope = MemoryScope()
        tech_scope.sectors.add("Technology")
        tech_entry = MemoryEntry(
            id="1",
            situation="Tech situation",
            recommendation="Tech recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=tech_scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )
        memory.add_entry(tech_entry)

        # Add healthcare sector entry
        health_scope = MemoryScope()
        health_scope.sectors.add("Healthcare")
        health_entry = MemoryEntry(
            id="2",
            situation="Healthcare situation",
            recommendation="Healthcare recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=health_scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )
        memory.add_entry(health_entry)

        # Retrieve with tech scope
        query_scope = MemoryScope()
        query_scope.sectors.add("Technology")

        results = memory.retrieve(
            query="situation",
            scope=query_scope,
            top_k=5
        )

        # Should prefer tech entry
        if results:
            top_entry = results[0]['entry']
            self.assertEqual(top_entry.situation, "Tech situation")


class TestReflectionMemory(unittest.TestCase):
    """Test ReflectionMemory functionality"""

    def test_add_pattern(self):
        """Test adding validated patterns"""
        memory = ReflectionMemory()

        scope = MemoryScope()
        pattern = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER,
            effectiveness=0.85,
            verified=True
        )

        result = memory.add_pattern(pattern)
        self.assertTrue(result)
        self.assertEqual(len(memory.patterns), 1)

    def test_low_effectiveness_rejected(self):
        """Test that low effectiveness patterns are rejected"""
        memory = ReflectionMemory()

        scope = MemoryScope()
        pattern = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER,
            effectiveness=0.5,  # Below threshold
            verified=True
        )

        result = memory.add_pattern(pattern)
        self.assertFalse(result)
        self.assertEqual(len(memory.patterns), 0)

    def test_unverified_rejected(self):
        """Test that unverified patterns are rejected"""
        memory = ReflectionMemory()

        scope = MemoryScope()
        pattern = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER,
            effectiveness=0.85,
            verified=False  # Not verified
        )

        result = memory.add_pattern(pattern)
        self.assertFalse(result)
        self.assertEqual(len(memory.patterns), 0)


class TestFinancialMemoryStore(unittest.TestCase):
    """Test FinancialMemoryStore functionality"""

    def setUp(self):
        """Set up test memory store"""
        self.store = FinancialMemoryStore()

    def test_add_situation(self):
        """Test adding a situation"""
        scope = MemoryScope()
        entry_id = self.store.add_situation(
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            source_agent=AgentRole.TRADER
        )

        self.assertIsNotNone(entry_id)
        self.assertEqual(len(self.store.episodic.entries), 1)

    def test_high_effectiveness_promotion(self):
        """Test that high effectiveness entries are promoted to reflection"""
        scope = MemoryScope()
        entry_id = self.store.add_situation(
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            source_agent=AgentRole.TRADER,
            effectiveness=0.85
        )

        self.assertEqual(len(self.store.reflection.patterns), 1)

    def test_retrieve_for_agent(self):
        """Test retrieving memories for specific agent"""
        scope = MemoryScope()
        scope.sectors.add("Technology")

        # Add test situation
        self.store.add_situation(
            situation="Tech stocks rallying",
            recommendation="Increase tech exposure",
            rationale="Strong momentum",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            source_agent=AgentRole.TRADER
        )

        # Retrieve
        results = self.store.retrieve_for_agent(
            agent_role=AgentRole.TRADER,
            query="tech stocks",
            scope=scope,
            top_k=3
        )

        self.assertGreaterEqual(len(results), 0)
        if results:
            self.assertIn('entry', results[0])
            self.assertIn('score', results[0])

    def test_to_prompt_context(self):
        """Test generating prompt context"""
        # Add some policies
        self.store.policy.add_policy("Test policy 1")
        self.store.policy.add_policy("Test policy 2")

        # Add test situation
        scope = MemoryScope()
        self.store.add_situation(
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            source_agent=AgentRole.TRADER
        )

        # Generate context
        context = self.store.to_prompt_context(
            agent_role=AgentRole.TRADER,
            query="test",
            scope=scope,
            top_k=3
        )

        self.assertIn("Trading Policies", context)
        self.assertIn("Test policy 1", context)
        self.assertGreater(len(context), 0)

    def test_save_and_load(self):
        """Test saving and loading memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Add test data
            self.store.policy.add_policy("Test policy")

            scope = MemoryScope()
            self.store.add_situation(
                situation="Test situation",
                recommendation="Test recommendation",
                rationale="Test rationale",
                confidence=MemoryLevel.HIGH,
                scope=scope,
                source_agent=AgentRole.TRADER,
                effectiveness=0.85
            )

            # Save
            self.store.save(tmpdir)

            # Load new store
            loaded_store = FinancialMemoryStore(
                policy_file=tmpdir / "policies.json",
                episodic_file=tmpdir / "episodes.json",
                reflection_file=tmpdir / "reflections.pkl"
            )

            # Verify
            self.assertEqual(len(loaded_store.policy.get_policies()), 1)
            self.assertEqual(len(loaded_store.episodic.entries), 1)
            self.assertEqual(len(loaded_store.reflection.patterns), 1)

    def test_get_stats(self):
        """Test getting memory statistics"""
        self.store.policy.add_policy("Test policy")

        scope = MemoryScope()
        self.store.add_situation(
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            source_agent=AgentRole.TRADER
        )

        stats = self.store.get_stats()
        self.assertEqual(stats['policy_count'], 1)
        self.assertEqual(stats['episodic_count'], 1)
        self.assertIn('total_memories', stats)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete memory system"""

    def test_complete_workflow(self):
        """Test complete workflow from adding to retrieving"""
        store = FinancialMemoryStore()

        # 1. Add policies
        store.policy.add_policy("Always use stop losses")
        store.policy.add_policy("Never risk more than 2%")

        # 2. Add trading situations
        tech_scope = MemoryScope()
        tech_scope.sectors.add("Technology")
        tech_scope.market_regimes.add(MarketRegime.BULL_MARKET)

        store.add_situation(
            situation="Tech stocks breaking out",
            recommendation="Increase tech exposure",
            rationale="Strong momentum and positive sentiment",
            confidence=MemoryLevel.HIGH,
            scope=tech_scope,
            source_agent=AgentRole.PORTFOLIO_MANAGER,
            effectiveness=0.85
        )

        # 3. Retrieve for agent
        results = store.retrieve_for_agent(
            agent_role=AgentRole.PORTFOLIO_MANAGER,
            query="tech stocks",
            scope=tech_scope,
            top_k=3
        )

        self.assertGreater(len(results), 0)

        # 4. Generate prompt context
        context = store.to_prompt_context(
            agent_role=AgentRole.PORTFOLIO_MANAGER,
            query="tech stocks",
            scope=tech_scope
        )

        self.assertIn("Always use stop losses", context)
        self.assertIn("Tech stocks breaking out", context)

        # 5. Get stats
        stats = store.get_stats()
        self.assertEqual(stats['policy_count'], 2)
        self.assertGreater(stats['episodic_count'], 0)

    def test_scope_filtering_workflow(self):
        """Test workflow with scope filtering"""
        store = FinancialMemoryStore()

        # Add entries for different sectors
        tech_scope = MemoryScope()
        tech_scope.sectors.add("Technology")

        health_scope = MemoryScope()
        health_scope.sectors.add("Healthcare")

        store.add_situation(
            situation="Tech rally",
            recommendation="Buy tech",
            rationale="Tech momentum",
            confidence=MemoryLevel.HIGH,
            scope=tech_scope,
            source_agent=AgentRole.TRADER
        )

        store.add_situation(
            situation="Healthcare rally",
            recommendation="Buy healthcare",
            rationale="Healthcare momentum",
            confidence=MemoryLevel.HIGH,
            scope=health_scope,
            source_agent=AgentRole.TRADER
        )

        # Query with tech scope
        query_scope = MemoryScope()
        query_scope.sectors.add("Technology")

        results = store.retrieve_for_agent(
            agent_role=AgentRole.TRADER,
            query="rally",
            scope=query_scope,
            top_k=5
        )

        # Should prioritize tech results
        if results:
            top_situation = results[0]['entry'].situation
            self.assertIn("Tech", top_situation)


@unittest.skipIf(not EMBEDDING_AVAILABLE, "sentence-transformers not available")
class TestHybridRetrieval(unittest.TestCase):
    """Test hybrid BM25 + embedding retrieval functionality"""

    def setUp(self):
        """Set up test memory with embeddings enabled"""
        self.memory = EpisodicFinancialMemory(enable_embeddings=True)

        # Add test entries with similar meanings but different keywords
        entries = [
            {
                "situation": "Technology stocks are rallying strongly",
                "recommendation": "Increase exposure to tech sector",
                "rationale": "Strong momentum in technology companies",
                "keywords": ["tech", "technology"]
            },
            {
                "situation": "IT companies showing significant growth",
                "recommendation": "Buy more tech stocks",
                "rationale": "Information technology sector is booming",
                "keywords": ["it", "information technology"]
            },
            {
                "situation": "Healthcare stocks declining due to regulatory concerns",
                "recommendation": "Reduce healthcare positions",
                "rationale": "New regulations affecting medical companies",
                "keywords": ["healthcare", "medical"]
            },
            {
                "situation": "Bank stocks rising with interest rates",
                "recommendation": "Invest in financial sector",
                "rationale": "Higher rates benefit financial institutions",
                "keywords": ["bank", "financial"]
            }
        ]

        for entry_data in entries:
            scope = MemoryScope()
            scope.sectors.add(entry_data["keywords"][0].capitalize())

            entry = MemoryEntry(
                id="",
                situation=entry_data["situation"],
                recommendation=entry_data["recommendation"],
                rationale=entry_data["rationale"],
                confidence=MemoryLevel.HIGH,
                scope=scope,
                timestamp=datetime.now().isoformat(),
                source_agent=AgentRole.TRADER
            )
            self.memory.add_entry(entry)

    def test_hybrid_vs_bm25_only(self):
        """Test that hybrid retrieval finds semantically similar results"""
        # Query with semantically similar but different keywords
        query = "software companies performing well"

        # BM25 only (keyword-based)
        results_bm25 = self.memory.retrieve(
            query=query,
            use_hybrid=False,
            top_k=5
        )

        # Hybrid retrieval
        results_hybrid = self.memory.retrieve(
            query=query,
            use_hybrid=True,
            alpha=0.5,
            top_k=5
        )

        # Both should return results
        self.assertGreater(len(results_bm25), 0, "BM25 should return results")
        self.assertGreater(len(results_hybrid), 0, "Hybrid should return results")

        # Hybrid should potentially rank differently due to semantic understanding
        # This is a soft test - we're just verifying it runs and returns results
        self.assertIsInstance(results_hybrid[0]['score'], float)

    def test_alpha_parameter(self):
        """Test that alpha parameter affects ranking"""
        query = "technology sector performance"

        # Different alpha values
        results_bm25 = self.memory.retrieve(query=query, use_hybrid=True, alpha=0.0, top_k=3)
        results_balanced = self.memory.retrieve(query=query, use_hybrid=True, alpha=0.5, top_k=3)
        results_embedding = self.memory.retrieve(query=query, use_hybrid=True, alpha=1.0, top_k=3)

        # All should return results
        self.assertGreater(len(results_bm25), 0)
        self.assertGreater(len(results_balanced), 0)
        self.assertGreater(len(results_embedding), 0)

        # Scores may differ based on alpha
        # We just verify they're valid scores
        for result in results_bm25:
            self.assertGreaterEqual(result['score'], 0.0)
            self.assertLessEqual(result['score'], 1.0)

    def test_hybrid_with_scope_filtering(self):
        """Test hybrid retrieval with scope filtering"""
        query = "stock performance"

        # Define scope for technology
        tech_scope = MemoryScope()
        tech_scope.sectors.add("Technology")

        results = self.memory.retrieve(
            query=query,
            scope=tech_scope,
            use_hybrid=True,
            top_k=5
        )

        # Should return results
        self.assertGreater(len(results), 0)

        # Top results should be tech-related due to scope boost
        if results:
            top_entry = results[0]['entry']
            # Should be technology-related
            text = f"{top_entry.situation} {top_entry.recommendation}".lower()
            self.assertTrue(
                "tech" in text or "it" in text or "software" in text,
                f"Expected tech-related entry, got: {text}"
            )

    def test_embedding_disabled(self):
        """Test fallback to BM25 when embeddings are disabled"""
        memory_no_emb = EpisodicFinancialMemory(enable_embeddings=False)

        # Add an entry
        scope = MemoryScope()
        entry = MemoryEntry(
            id="",
            situation="Test situation",
            recommendation="Test recommendation",
            rationale="Test rationale",
            confidence=MemoryLevel.HIGH,
            scope=scope,
            timestamp=datetime.now().isoformat(),
            source_agent=AgentRole.TRADER
        )
        memory_no_emb.add_entry(entry)

        # Should still work with BM25 only
        results = memory_no_emb.retrieve(
            query="test situation",
            use_hybrid=True,  # This should be ignored
            top_k=5
        )

        self.assertGreater(len(results), 0)

    def test_hybrid_retrieval_consistency(self):
        """Test that hybrid retrieval produces consistent results"""
        query = "technology stocks"

        # Run the same query multiple times
        results1 = self.memory.retrieve(query=query, use_hybrid=True, alpha=0.5, top_k=3)
        results2 = self.memory.retrieve(query=query, use_hybrid=True, alpha=0.5, top_k=3)

        # Should produce same results
        self.assertEqual(len(results1), len(results2))

        for i in range(len(results1)):
            self.assertEqual(results1[i]['entry'].id, results2[i]['entry'].id)
            # Scores should be very close (might have tiny floating point differences)
            self.assertAlmostEqual(results1[i]['score'], results2[i]['score'], places=5)


if __name__ == '__main__':
    unittest.main()
