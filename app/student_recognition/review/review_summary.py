from dataclasses import dataclass
@dataclass(frozen=True)
class ReviewSummary: total:int; unresolved:int; resolved:int
def summarize(queue):
    total=len(queue.all());unresolved=queue.pending_count();return ReviewSummary(total,unresolved,total-unresolved)
