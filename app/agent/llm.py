"""Claude API-тай холбогдох нэг цэг. Түлхүүр эсвэл anthropic сан байхгүй бол None буцаана → демо горим."""
import os

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")

_client = None


def get_client():
    global _client
    if _client is not None:
        return _client
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    _client = anthropic.Anthropic()
    return _client


def is_live() -> bool:
    return get_client() is not None
