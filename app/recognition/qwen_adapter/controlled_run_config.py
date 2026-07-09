"""R21: Controlled Qwen run config — fail-closed by default."""
from dataclasses import dataclass, field


@dataclass
class ControlledQwenRunConfig:
    allow_real_api: bool = False
    image_path: str = ""
    api_key_env: str = ""
    output_path: str = ""
    request_id: str = ""
    max_image_bytes: int = 10 * 1024 * 1024  # 10 MB
    save_raw_response: bool = False
    emit_base64: bool = False

    def validate(self) -> list:
        errors = []
        if not self.allow_real_api:
            errors.append("allow_real_api is False — real API disabled")
        if not self.image_path:
            errors.append("image_path is required for real API call")
        if not self.api_key_env:
            errors.append("api_key_env is required for real API call")
        if self.save_raw_response:
            errors.append("save_raw_response must be False — safety violation")
        if self.emit_base64:
            errors.append("emit_base64 must be False — safety violation")
        return errors

    def can_run(self) -> bool:
        return len(self.validate()) == 0
