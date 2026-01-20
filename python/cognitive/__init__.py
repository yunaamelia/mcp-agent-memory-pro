"""
Cognitive Features Module - Phase 3

Provides advanced AI-powered memory intelligence including:
- Graph Query Engine: Multi-hop relationship traversal and graph analysis
- Context Analyzer: Proactive context understanding and memory recall
- Suggestion Engine: Smart recommendations and issue detection
- Pattern Detector: Behavior pattern recognition and anomaly detection
- Clustering Service: Memory clustering and similarity grouping
- Consolidation Service: Memory deduplication and abstraction
"""

from .clustering_service import ClusteringService
from .consolidation_service import ConsolidationService
from .context_analyzer import ContextAnalyzer
from .graph_engine import GraphQueryEngine
from .pattern_detector import PatternDetector
from .suggestion_engine import SuggestionEngine

__all__ = [
    "ClusteringService",
    "ConsolidationService",
    "ContextAnalyzer",
    "GraphQueryEngine",
    "PatternDetector",
    "SuggestionEngine",
]
