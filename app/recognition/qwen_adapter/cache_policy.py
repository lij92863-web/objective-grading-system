"""R98A: Qwen cache key policy."""
import hashlib
from dataclasses import dataclass


@dataclass
class CacheKey:
    image_sha256: str = ""
    roi_id: str = ""
    prompt_version: str = "v1"
    engine_name: str = "qwen"
    candidate_kind: str = ""

    def to_key(self) -> str:
        raw = f"{self.image_sha256}|{self.roi_id}|{self.prompt_version}|{self.engine_name}|{self.candidate_kind}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def safe_for_log(self) -> str:
        return self.to_key()


def build_cache_key(image_sha256: str, roi_id: str, prompt_version: str = "v1",
                     engine_name: str = "qwen", candidate_kind: str = "") -> CacheKey:
    return CacheKey(image_sha256=image_sha256, roi_id=roi_id,
                     prompt_version=prompt_version, engine_name=engine_name,
                     candidate_kind=candidate_kind)
