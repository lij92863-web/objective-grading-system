import dataclasses


@dataclasses.dataclass(frozen=True)
class PipelineEvent:
    event_type: str
    capture_job_id: str
    detail: str
