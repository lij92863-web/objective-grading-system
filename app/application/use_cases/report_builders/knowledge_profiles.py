"""Knowledge profiles builder — matches legacy ``build_knowledge_profiles``."""

from collections import defaultdict


def _mastery_level(mastery: float) -> str:
    if mastery < 40: return "严重薄弱"
    if mastery < 60: return "明显薄弱"
    if mastery < 80: return "基本掌握"
    return "掌握较好"


def build_knowledge_profiles(questions: list, results: list, weak_threshold: float = 70.0) -> list:
    """Return knowledge profile dicts matching legacy ``build_knowledge_profiles``.

    *questions*: list of dicts with question (int), tags (list), points.
    *results*: list of dicts with student_id, name, details (list of dicts with number, score, max_score).
    """
    by_number = {q["question"]: q for q in questions}
    profiles = []
    for result in results:
        tag_scores = defaultdict(float)
        tag_max = defaultdict(float)
        tag_counts = defaultdict(int)
        for d in result.get("details", []):
            if d.get("max_score", 0) <= 0: continue
            qnum = d.get("number", d.get("question"))
            spec = by_number.get(qnum, {})
            tags = spec.get("tags", ["untagged"]) or ["untagged"]
            if isinstance(tags, str): tags = [t.strip() for t in tags.split(";") if t.strip()] or ["untagged"]
            for tag in tags:
                tag_scores[tag] += d.get("score", 0)
                tag_max[tag] += d.get("max_score", 0)
                tag_counts[tag] += 1
        for tag in sorted(tag_max):
            mx = tag_max[tag]
            mastery = round(tag_scores[tag] / mx * 100, 2) if mx else 0.0
            profiles.append(dict(
                student_id=result["student_id"],
                name=result["name"],
                tag=tag,
                score=round(tag_scores[tag], 4),
                max_score=round(mx, 4),
                mastery=mastery,
                question_count=tag_counts[tag],
                weak="yes" if mastery < weak_threshold else "no",
                mastery_level=_mastery_level(mastery),
            ))
    return profiles
