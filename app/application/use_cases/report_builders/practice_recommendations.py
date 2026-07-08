"""Practice recommendations builder — matches legacy
``build_correct_question_ids``, ``build_target_difficulties``,
and ``recommend_practice``.
"""

import statistics
from collections import defaultdict


def build_correct_question_ids(questions: list, results: list) -> dict:
    """Return {student_id: set(question_id)} for correctly answered questions."""
    by_number = {q["question"]: q for q in questions}
    correct_ids = defaultdict(set)
    for result in results:
        for d in result.get("details", []):
            if d.get("max_score", 0) <= 0: continue
            spec = by_number.get(d.get("number", d.get("question")), {})
            sid = spec.get("source_id", "")
            if sid and d.get("status") == "correct":
                correct_ids[result["student_id"]].add(sid)
    return dict(correct_ids)


def build_target_difficulties(questions: list, results: list) -> dict:
    """Return {(student_id, tag): target_difficulty_int} for missed questions."""
    by_number = {q["question"]: q for q in questions}
    misses = defaultdict(list)
    for result in results:
        for d in result.get("details", []):
            if d.get("max_score", 0) <= 0: continue
            if d.get("status") == "correct": continue
            spec = by_number.get(d.get("number", d.get("question")), {})
            diff = spec.get("difficulty", 0)
            if not diff: continue
            tags = spec.get("tags", ["untagged"]) or ["untagged"]
            if isinstance(tags, str): tags = [t.strip() for t in tags.split(";") if t.strip()] or ["untagged"]
            for tag in tags:
                misses[(result["student_id"], tag)].append(diff)
    return {k: int(round(statistics.mean(v))) for k, v in misses.items()}


def _difficulty_rank(q_diff: int, target_diff: int) -> tuple:
    if not target_diff or not q_diff: return (9, 9, q_diff or 9)
    if q_diff == target_diff: return (0, 0, q_diff)
    if q_diff == target_diff - 1: return (1, 0, q_diff)
    return (2, abs(q_diff - target_diff), q_diff)


def build_practice_recommendations(profiles: list, question_bank: list, per_tag: int = 3,
                                    already_correct: dict = None,
                                    target_difficulties: dict = None) -> list:
    """Return practice recommendation rows matching legacy ``recommend_practice``."""
    already_correct = already_correct or {}
    target_difficulties = target_difficulties or {}
    bank_by_tag = defaultdict(list)
    for q in question_bank:
        tags = q.get("tags", []) or []
        if isinstance(tags, str): tags = [t.strip() for t in tags.split(";") if t.strip()]
        for tag in tags:
            bank_by_tag[tag].append(q)

    rows = []
    weak = sorted(profiles, key=lambda p: (p.get("student_id", ""), p.get("mastery", 0), p.get("tag", "")))
    for profile in weak:
        if not profile.get("weak"): continue
        tag = profile.get("tag", "")
        target_diff = target_difficulties.get((profile.get("student_id", ""), tag), 0)
        selected = 0
        candidates = sorted(
            bank_by_tag.get(tag, []),
            key=lambda q: _difficulty_rank(q.get("difficulty", 0), target_diff),
        )
        for q in candidates:
            if q.get("question_id", "") in already_correct.get(profile.get("student_id", ""), set()):
                continue
            q_diff = q.get("difficulty", 0)
            rows.append(dict(
                student_id=profile["student_id"],
                name=profile.get("name", ""),
                weak_tag=tag,
                mastery=profile.get("mastery", 0),
                question_id=q.get("question_id", ""),
                target_difficulty=target_diff,
                difficulty=q_diff,
                difficulty_delta=abs(q_diff - target_diff) if target_diff else "",
                stem=q.get("stem", ""),
                answer=q.get("answer", ""),
                tags=";".join(q.get("tags", []) if isinstance(q.get("tags"), list) else []),
            ))
            selected += 1
            if selected >= per_tag: break
    return rows
