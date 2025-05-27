#!/usr/bin/env python3
"""Integration tests for knowledge_manager modules."""

import sys
import os
from pathlib import Path
import unittest
import pytest

# ensure env vars exist prior to importing project modules
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("TELEGRAM_TOKEN", "test")
os.environ.setdefault("QDRANT_API_KEY", "test")
os.environ.setdefault("QDRANT_IS_CLOUD", "false")

pytest.importorskip("langchain_community", reason="langchain_community not installed")

project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
for p in (project_root, src_path):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.config.env_manager import init_config
from src.knowledge_manager.ttl_cleaner import clean_expired_points
from src.knowledge_manager.delete_old_points import delete_old_points
from src.knowledge_manager.cluster_merger import cluster_and_merge
from src.knowledge_manager.conflict_detector import detect_conflicts
class TestKnowledgeManager(unittest.TestCase):
    """Run operations that touch the vector DB with real APIs."""

    @classmethod
    def setUpClass(cls):
        cls.config = init_config(test_mode=False)

    def test_cluster_and_merge(self):
        cluster_and_merge(n_clusters=1)

    def test_ttl_cleaner(self):
        clean_expired_points()

    def test_delete_old_points(self):
        delete_old_points()

    def test_detect_conflicts(self):
        conflicts = detect_conflicts()
        self.assertIsInstance(conflicts, list)


if __name__ == "__main__":
    unittest.main()
