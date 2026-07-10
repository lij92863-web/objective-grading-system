"""Debug artifact metadata only; production persistence is a later concern."""
from dataclasses import dataclass
from typing import Optional
@dataclass(frozen=True)
class DebugArtifacts: overlay_path:Optional[str]=None
