"""R24: Controlled Qwen client — fail-closed, no .env, no raw save."""
import os, uuid
from dataclasses import dataclass, field
from .controlled_run_config import ControlledQwenRunConfig


@dataclass
class ControlledQwenResult:
    request_id: str = ""
    status: str = "disabled"
    error: str = ""
    candidates: list = field(default_factory=list)
    sha256: str = ""


class ControlledQwenClient:
    """Safe client — requires explicit config to run."""
    def __init__(self, config: ControlledQwenRunConfig = None):
        self.config = config or ControlledQwenRunConfig()

    def run(self) -> ControlledQwenResult:
        if not self.config.allow_real_api:
            return ControlledQwenResult(request_id=str(uuid.uuid4())[:8],
                                        status="disabled",
                                        error="Real API disabled; pass --allow-real-api")

        errors = self.config.validate()
        if errors:
            return ControlledQwenResult(status="blocked", error="; ".join(errors))

        # Real call would go here — NOT IMPLEMENTED this round
        return ControlledQwenResult(request_id=str(uuid.uuid4())[:8],
                                     status="not_executed",
                                     error="Real Qwen endpoint not configured")


class FakeQwenClient:
    """Always returns controlled fake responses for testing."""
    def run(self, choice_response=None, blank_response=None, identity_response=None):
        return ControlledQwenResult(request_id="fake-001", status="ok",
                                     candidates=choice_response or [],
                                     sha256="fake-sha256")
