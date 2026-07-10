from dataclasses import dataclass
@dataclass(frozen=True)
class OCRPolicy: allow_real_client:bool=False; save_raw_response:bool=False; save_base64:bool=False
DEFAULT_OCR_POLICY=OCRPolicy()
