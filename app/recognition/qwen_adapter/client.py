"""Abstract Qwen client interface.

Defines the contract that both the fake client and the future real client
must fulfil.  Concrete implementations live in ``fake_client.py`` (mock
stage) and (later) ``real_client.py``.
"""

from abc import ABC, abstractmethod

from .models import QwenRawResponse, QwenRequest


class QwenClient(ABC):
    """Abstract interface for Qwen API calls.

    Each method corresponds to one prompt type and returns a raw response.
    Parsing and validation are handled separately in ``parser.py`` and
    ``validators.py``.
    """

    @abstractmethod
    def recognize_name_field(self, request: QwenRequest) -> QwenRawResponse:
        """Recognize the name-field area of an answer sheet."""
        ...

    @abstractmethod
    def recognize_choice_cell(self, request: QwenRequest) -> QwenRawResponse:
        """Recognize a single choice-cell answer."""
        ...

    @abstractmethod
    def recognize_blank_answer(self, request: QwenRequest) -> QwenRawResponse:
        """Recognize a fill-in-the-blank answer."""
        ...

    @abstractmethod
    def judge_complex_blank(self, request: QwenRequest) -> QwenRawResponse:
        """Judge whether a complex blank answer is mathematically equivalent."""
        ...
