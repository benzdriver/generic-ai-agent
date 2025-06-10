# Refactoring Progress

This document tracks the progress of the codebase refactoring.

## Phase 1: Architecture & Structure

- [x] **Global**: Clarify and document the official project structure vs. what is in the README.
- [x] **Global**: Add type hinting across the entire codebase.
- [x] **Global**: Implement a centralized, dependency-injected client for services (LLM, VectorDB).
- [x] **Config**: Consolidate `env_manager.py` and `domain_manager.py` into a single, unified config module.
- [x] **Config**: Use Pydantic for loading and validating all configurations.
- [x] **Vector Engine**: Create a `base_vector_store.py` with an abstract interface for vector operations.
- [x] **Vector Engine**: Refactor `qdrant_client.py` into a `qdrant_vector_store.py` that implements the base interface.
- [x] **Vector Engine**: Update `retriever.py` and `vector_indexer.py` to use the abstract interface.
- [x] **Agent Core**: Create a `llm.py` or `llm_client.py` module with a base class for LLM interactions.
- [x] **Agent Core**: Create concrete implementations for different LLM providers (e.g., `openai_client.py`).
- [x] **Agent Core**: Refactor `response_router.py` to use the LLM client via dependency injection.
- [x] **Agent Core**: Rename `canonical_router.py` to `query_normalizer.py` for clarity.
- [x] **Knowledge Manager**: Refactor `cluster_merger.py` to use the abstract LLM client.
- [x] **Knowledge Manager**: Document the purpose of `conflict_detector.py` in the README.
- [x] **Tests**: Add unit tests for each module, focusing on business logic.
- [x] **Tests**: Mock external services (LLM, VectorDB) in tests to make them faster and more reliable.
- [x] **Tests**: Add integration tests for the full RAG pipeline. 