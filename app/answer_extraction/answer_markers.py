from __future__ import annotations

import re

REAL_CHINESE_ANSWER_MARKER = "【答案】"

COMPAT_ANSWER_MARKERS = (
    "〖答案〗",
    "[答案]",
)

ANSWER_MARKERS = (
    REAL_CHINESE_ANSWER_MARKER,
    *COMPAT_ANSWER_MARKERS,
)


def build_answer_marker_regex() -> str:
    """Return a regex alternation that matches supported explicit answer markers.

    Important:
    - 【答案】 is the real, primary marker used in teacher files.
    - 〖答案〗 and [答案] are compatibility markers only.
    - Do not rename compatibility marker tests as real_chinese_brackets.
    """
    return "(?:" + "|".join(re.escape(marker) for marker in ANSWER_MARKERS) + ")"


def is_real_chinese_answer_marker(text: str) -> bool:
    return REAL_CHINESE_ANSWER_MARKER in text


# Pre-built regex for consumers that need the compiled pattern.
ANSWER_MARKER_RE = re.compile(build_answer_marker_regex())
