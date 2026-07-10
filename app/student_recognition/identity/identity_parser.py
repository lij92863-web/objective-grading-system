import re
from .identity_candidate import IdentityCandidate
PATTERNS=(re.compile(r'^\s*(\d+)\s*([^\d\s]+)\s*$'),re.compile(r'^\s*学号\s*(\d+)\s*姓名\s*(\S+)\s*$'))
def parse_identity_text(text,source='manual',confidence=1.0):
    raw=text or ''
    for pattern in PATTERNS:
        match=pattern.match(raw)
        if match:return IdentityCandidate(match.group(1),match.group(2),source,confidence,raw)
    name=raw.strip() or None
    return IdentityCandidate(None,name,source,confidence,raw)
