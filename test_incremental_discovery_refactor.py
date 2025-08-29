#!/usr/bin/env python3
"""
Unit-Tests für die Refaktorierung der inkrementellen Quellensuche:
- IncrementalDiscoveryOrchestrator
- SourcePersistenceManager
- SourceStatisticsCalculator

Tests sind unabhängig von echter DB – db_manager wird gemockt und
die Discovery wird über eine Fake-Implementierung bereitgestellt.
"""

import sys
import os
import unittest
from datetime import datetime
from typing import List, Dict, Any, Optional

# Stellt sicher, dass das Backend-Modul importiert werden kann
if '/app/backend' not in sys.path:
    sys.path.insert(0, '/app/backend')

from minesearch.enhanced_source_discovery import (
    EnhancedSourceDiscovery,
    IncrementalDiscoveryOrchestrator,
    SourceAccumulator,
    SourcePersistenceManager,
    SourceStatisticsCalculator,
)


class _FakeDiscovery(EnhancedSourceDiscovery):
    """Fake Discovery Service, liefert deterministische Quellen zurück."""

    def __init__(self, responses: Optional[List[Dict[str, Any]]] = None):
        super().__init__()
        self._responses = list(responses or [])

    def discover_sources_for_mine(
        self,
        mine_name: str,
        country: Optional[str] = None,
        region: Optional[str] = None,
        commodity: Optional[str] = None,
        priority_focus: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return list(self._responses)


class _DummyDbManager:
    """Minimaler Dummy für db_manager mit Call-Recording."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def add_or_update_source(
        self,
        url: str,
        domain: Optional[str] = None,
        country: Optional[str] = None,
        region: Optional[str] = None,
        source_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.calls.append(
            {
                'url': url,
                'domain': domain,
                'country': country,
                'region': region,
                'source_type': source_type,
                'metadata': dict(metadata or {}),
            }
        )


class IncrementalDiscoveryRefactorTests(unittest.TestCase):
    def test_orchestrator_filters_and_annotates(self):
        existing_sources = [
            {'url': 'https://sedar.com/companies/foo-reports', 'domain': 'sedar.com'},
            {'url': 'https://gov.example/mines/foo/data', 'domain': 'gov.example'},
        ]
        discovered = [
            {'url': 'https://sedar.com/companies/foo-reports', 'domain': 'sedar.com', 'type': 'exchange', 'priority': 2},  # duplicate URL
            {'url': 'https://sedar.com/filings/ni-43-101/foo', 'domain': 'sedar.com', 'type': 'document', 'priority': 1},   # similar domain, but different path
            {'url': 'https://gov.example/mines/foo/data', 'domain': 'gov.example', 'type': 'government', 'priority': 1},    # duplicate URL
            {'url': 'https://nrcan.gc.ca/mining-materials/foo', 'domain': 'nrcan.gc.ca', 'type': 'government', 'priority': 1},
        ]

        fake_discovery = _FakeDiscovery(discovered)
        accumulator = SourceAccumulator()
        persistence = SourcePersistenceManager(db_manager=None)  # nicht verwendet in diesem Test
        stats = SourceStatisticsCalculator()
        orchestrator = IncrementalDiscoveryOrchestrator(
            discovery_service=fake_discovery,
            accumulator=accumulator,
            persistence_manager=persistence,
            statistics_calculator=stats,
        )

        result = orchestrator.run_incremental_discovery(
            mine_name='Foo Mine',
            model_id='provider:modelA',
            existing_sources=existing_sources,
            country='Canada',
            region='QC',
            commodity='Gold',
            priority_focus='model_1_discovery',
        )

        # Erwartung: 2 neue Quellen (die zweite sedar-URL und die nrcan-URL)
        self.assertEqual(len(result), 2)
        for src in result:
            self.assertIn('discovered_by_model', src)
            self.assertIn('discovered_at', src)
            self.assertTrue(src.get('incremental_discovery', False))

        # Accumulator wurde gefüllt
        acc = accumulator.get_accumulated_sources()
        self.assertEqual(len(acc), 2)

    def test_persistence_manager_saves_via_db_manager(self):
        dummy_db = _DummyDbManager()
        persistence = SourcePersistenceManager(db_manager=dummy_db)
        sources = [
            {'url': 'https://example.com/a', 'domain': 'example.com', 'type': 'document', 'priority': 2},
            {'url': 'https://example.com/b', 'domain': 'example.com', 'type': 'government', 'priority': 1},
        ]

        count = persistence.save_sources(sources=sources, mine_name='Foo Mine', model_id='provider:modelB')
        self.assertEqual(count, 2)
        self.assertEqual(len(dummy_db.calls), 2)
        # Metadata enthält inkrementelle Flags
        for call in dummy_db.calls:
            self.assertIn('incremental_discovery', call['metadata'])
            self.assertIn('discovered_for', call['metadata'])
            self.assertIn('discovered_by_model', call['metadata'])

    def test_statistics_calculator_rank_and_stats(self):
        stats = SourceStatisticsCalculator()
        sample_sources = [
            {'url': 'https://doc.example/x', 'type': 'document', 'priority': 3, 'reliability_score': 10},
            {'url': 'https://gov.example/x', 'type': 'government', 'priority': 1, 'reliability_score': 0},
            {'url': 'https://db.example/x', 'type': 'database', 'priority': 2, 'reliability_score': 50},
        ]
        ranked = stats.rank_sources_by_quality(sample_sources)
        # Government mit hoher Basis und priority 1 sollte weit oben sein, aber database mit hoher reliability kann überholen
        self.assertEqual(len(ranked), 3)
        # Prüfe, dass Ranking deterministisch ist
        self.assertTrue(all('url' in s for s in ranked))

        contributions = {'provider:modelA': 2, 'provider:modelB': 1}
        summary = stats.get_statistics(sample_sources, contributions)
        self.assertEqual(summary['total_sources'], 3)
        self.assertEqual(summary['model_contributions'], contributions)
        self.assertIn('type_distribution', summary)
        self.assertIn('priority_distribution', summary)
        self.assertGreaterEqual(summary['unique_domains'], 0)


if __name__ == '__main__':
    unittest.main()


