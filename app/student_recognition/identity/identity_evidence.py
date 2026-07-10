from dataclasses import dataclass
@dataclass(frozen=True)
class IdentityEvidence: roi_crop_path:str; image_hash:str; raw_text:str
