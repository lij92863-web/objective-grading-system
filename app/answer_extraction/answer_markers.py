from __future__ import annotations

import re

REAL_CHINESE_ANSWER_MARKER = "【答案】"

# AE590 verified literal marker: REAL must be 【答案】 (U+3010/U+3011).

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


def _assert_marker_codepoints() -> None:
    """Import-time guard against accidental 【】/〖〗 bracket swaps.

    REAL must use black lenticular brackets 【】(U+3010/U+3011);
    compatibility markers must use white lenticular brackets 〖〗(U+3016/U+3017).
    """
    if not (REAL_CHINESE_ANSWER_MARKER[0] == "\u3010" and REAL_CHINESE_ANSWER_MARKER[-1] == "\u3011"):
        raise AssertionError(
            "REAL_CHINESE_ANSWER_MARKER must use black lenticular brackets "
            "\u3010\u3011 (U+3010/U+3011), got %r" % REAL_CHINESE_ANSWER_MARKER
        )
    for _marker in COMPAT_ANSWER_MARKERS:
        if _marker[0] == "\u3010" and _marker[-1] == "\u3011":
            raise AssertionError(
                "Compatibility marker must not use black lenticular brackets "
                "\u3010\u3011 (U+3010/U+3011), got %r" % _marker
            )


_assert_marker_codepoints()
