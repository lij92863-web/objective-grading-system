"""Multi-candidate fusion for recognition drafts (constitution §2, draft layer).

Pure function: merges several candidate maps (e.g. from multiple crops / passes)
into one. Later non-``None`` values win; differing non-``None`` values for the
same key are recorded as conflicts for downstream review. Contains no IO and no
recognition algorithm.
"""

from typing import Any, Dict, List, Tuple


def fuse_candidates(
    candidate_maps: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], List[str]]:
    """Fuse ``candidate_maps`` into ``(fused, conflicts)``.

    * ``None`` values are ignored.
    * A later concrete value overrides an earlier one.
    * If two concrete values for the same key differ, the key is added to
      ``conflicts`` (the caller should turn conflicts into review items).
    """
    fused: Dict[str, Any] = {}
    conflicts: List[str] = []
    for cmap in candidate_maps:
        if not cmap:
            continue
        for key, value in cmap.items():
            if value is None:
                continue
            if key in fused and fused[key] is not None and fused[key] != value:
                if key not in conflicts:
                    conflicts.append(key)
            fused[key] = value
    return fused, conflicts
