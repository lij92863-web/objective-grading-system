"""No-real-API guard — prevent accidental real Qwen calls."""
from .qwen_adapter.real_client import RealQwenClient


def assert_no_real_qwen_by_default():
    """RealQwenClient must be disabled by default."""
    c = RealQwenClient()
    if c.enabled:
        raise RuntimeError("RealQwenClient is enabled by default — safety violation")


def check_env_safety():
    import os
    if os.environ.get("QWEN_API_ENABLED", "").lower() == "true":
        raise RuntimeError("QWEN_API_ENABLED=true is not allowed in tests/scripts by default")
