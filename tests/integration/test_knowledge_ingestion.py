#!/usr/bin/env python3
"""Integration tests for knowledge_ingestion modules."""

import sys
import os
from pathlib import Path
import unittest

# set required environment variables before project imports
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("TELEGRAM_TOKEN", "test")
os.environ.setdefault("QDRANT_API_KEY", "test")
os.environ.setdefault("QDRANT_IS_CLOUD", "false")

project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
for p in (project_root, src_path):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.config.env_manager import init_config
from src.knowledge_ingestion.doc_parser import parse_html_content, store_document
from src.knowledge_ingestion.tagger import auto_tag


class TestKnowledgeIngestion(unittest.TestCase):
    """Test parsing and tagging with real services."""

    @classmethod
    def setUpClass(cls):
        cls.config = init_config(test_mode=False)

    def test_parse_and_store_document(self):
        html = "<html><body><p>This is a sample paragraph that is definitely long enough to generate an embedding.</p></body></html>"
        paragraphs = parse_html_content(html)
        self.assertGreater(len(paragraphs), 0)

        metadata = {"source": "integration_test", "doc_type": "test"}
        store_document(paragraphs[0], metadata)

    def test_auto_tag(self):
        text = "I currently hold a work permit and plan to apply for Express Entry."
        tags = auto_tag(text, domain="immigration")
        self.assertIsInstance(tags, list)


if __name__ == "__main__":
    unittest.main()
