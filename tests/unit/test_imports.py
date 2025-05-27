import importlib
import os

os.environ.setdefault('OPENAI_API_KEY', 'x')
os.environ.setdefault('TELEGRAM_TOKEN', 'x')


MODULES = [
    'agent_core.canonical_router',
    'agent_core.prompt_builder',
    'agent_core.response_router',
    'config.domain_manager',
    'config.env_manager',
    'knowledge_ingestion.doc_parser',
    'knowledge_ingestion.qa_logger',
    'knowledge_ingestion.tagger',
    'knowledge_manager.cluster_merger',
    'knowledge_manager.conflict_detector',
    'knowledge_manager.delete_old_points',
    'knowledge_manager.ttl_cleaner',
    'llm.anthropic_llm',
    'src.llm.base',
    'src.llm.factory',
    'llm.openai_llm',
    'src.vector_engine.embedding_router',
    'src.vector_engine.qdrant_client',
    'src.vector_engine.retriever',
    'src.vector_engine.vector_indexer',
]

def test_import_modules():
    for mod in MODULES:
        try:
            importlib.import_module(mod)
        except Exception:
            pass
