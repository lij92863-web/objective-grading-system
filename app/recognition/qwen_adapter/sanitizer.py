"""R25: Qwen response sanitizer — removes API keys, base64, raw response."""
import json, re
from pathlib import Path


FORBIDDEN_KEYS = {"api_key", "apikey", "authorization", "bearer", "token",
                   "secret", "password", "credential"}
FORBIDDEN_PATTERNS = [r"sk-[a-zA-Z0-9]{20,}", r"Bearer\s+\S+",
                       r"data:image/[a-z]+;base64,", r"^([A-Za-z0-9+/]{100,}=*)$"]


def sanitize_qwen_output(data: dict, image_path: str = "") -> dict:
    result = {}
    for k, v in data.items():
        if k.lower() in FORBIDDEN_KEYS:
            continue
        if isinstance(v, str):
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern, v):
                    v = "[REDACTED]"
            # Redact full local paths
            if image_path and image_path in v:
                v = v.replace(image_path, "[IMAGE_PATH]")
        result[k] = v
    result.pop("raw_response", None)
    result.pop("base64", None)
    return result


def sanitize_to_json(data: dict, output_path: str, image_path: str = "") -> None:
    clean = sanitize_qwen_output(data, image_path)
    clean["sanitized"] = True
    clean["image_sha256"] = data.get("sha256", "")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(clean, ensure_ascii=False, indent=2), "utf-8")
