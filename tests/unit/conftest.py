import sys
from pathlib import Path

# add project root to path
project_root = Path(__file__).resolve().parents[2]
src_path = project_root / 'src'
for p in (project_root, src_path):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

# provide default environment variables for config loading
import os
os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('TELEGRAM_TOKEN', 'test')
os.environ.setdefault('QDRANT_IS_CLOUD', 'false')
os.environ.setdefault('QDRANT_API_KEY', 'dummy')

# stub LLM provider modules to avoid heavy dependencies
import types
openai_stub = types.ModuleType('llm.openai_llm')
class _DummyLLM:
    def __init__(self, *a, **k):
        pass
    def generate(self, *a, **k):
        return 'stub'
    def generate_with_chunks(self, *a, **k):
        return 'stub'
    def chat(self, *a, **k):
        return 'stub'
openai_stub.OpenAILLM = _DummyLLM
anthropic_stub = types.ModuleType('llm.anthropic_llm')
anthropic_stub.AnthropicLLM = _DummyLLM
llm_pkg = types.ModuleType('llm')
llm_pkg.__path__ = [str(src_path / 'llm')]
sys.modules['llm'] = llm_pkg
sys.modules['llm.openai_llm'] = openai_stub
sys.modules['llm.anthropic_llm'] = anthropic_stub
