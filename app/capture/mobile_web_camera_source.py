import dataclasses
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Mapping

from .capture_queue import (
    CaptureClientConflictError,
    CaptureQueue,
    CaptureRegistration,
    CaptureSessionNotFoundError,
    CaptureSessionStateError,
)
from .capture_source import CaptureSourceType


MAX_MOBILE_CAPTURE_BYTES = 32 * 1024 * 1024
MAX_MOBILE_CAPTURE_REQUEST_BYTES = MAX_MOBILE_CAPTURE_BYTES + 64 * 1024
CLIENT_CAPTURE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ALLOWED_CAPTURE_METHODS = {"IMAGE_CAPTURE", "CANVAS"}
ALLOWED_FACING_MODES = {"environment", "user", "left", "right", "unknown"}
MIME_SUFFIXES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
}


class MobileCaptureError(ValueError):
    def __init__(self, message: str, status: int, code: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


@dataclasses.dataclass(frozen=True)
class MobileCaptureMetadata:
    client_capture_id: str
    captured_at: str
    capture_method: str
    device_label: str
    device_id: str
    facing_mode: str
    width: int
    height: int
    mime_type: str

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False, sort_keys=True)


class MobileWebCameraSource:
    def __init__(self, queue: CaptureQueue) -> None:
        self.queue = queue

    def upload_blob(
        self,
        session_id: str,
        filename: str,
        content: bytes,
        file_mime_type: str,
        fields: Mapping[str, str],
    ) -> CaptureRegistration:
        metadata = self._validate(filename, content, file_mime_type, fields)
        try:
            return self.queue.add_bytes(
                session_id,
                filename,
                content,
                CaptureSourceType.MOBILE_WEB_USB_CAMERA,
                client_capture_id=metadata.client_capture_id,
                metadata_json=metadata.to_json(),
            )
        except CaptureSessionNotFoundError as exc:
            raise MobileCaptureError("考试会话不存在。", 404, "SESSION_NOT_FOUND") from exc
        except CaptureSessionStateError as exc:
            raise MobileCaptureError(
                "当前考试状态不允许继续采集。",
                409,
                "SESSION_NOT_CAPTURE_READY",
            ) from exc
        except CaptureClientConflictError as exc:
            raise MobileCaptureError(
                "同一客户端采集编号对应了不同图片，已阻断上传。",
                409,
                "CLIENT_CAPTURE_ID_CONFLICT",
            ) from exc

    def _validate(
        self,
        filename: str,
        content: bytes,
        file_mime_type: str,
        fields: Mapping[str, str],
    ) -> MobileCaptureMetadata:
        if not content:
            raise MobileCaptureError("图片文件为空。", 400, "EMPTY_IMAGE")
        if len(content) > MAX_MOBILE_CAPTURE_BYTES:
            raise MobileCaptureError("图片超过 32 MiB 上限。", 413, "IMAGE_TOO_LARGE")
        client_capture_id = str(fields.get("client_capture_id", "")).strip()
        if not CLIENT_CAPTURE_ID_PATTERN.fullmatch(client_capture_id):
            raise MobileCaptureError(
                "client_capture_id 格式无效。",
                400,
                "INVALID_CLIENT_CAPTURE_ID",
            )
        captured_at = self._text(fields, "captured_at", 64, required=True)
        try:
            timestamp = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise MobileCaptureError(
                "captured_at 必须是 ISO-8601 时间。",
                400,
                "INVALID_CAPTURED_AT",
            ) from exc
        if timestamp.tzinfo is None:
            raise MobileCaptureError(
                "captured_at 必须包含时区。",
                400,
                "INVALID_CAPTURED_AT",
            )
        capture_method = self._text(fields, "capture_method", 32, required=True).upper()
        if capture_method not in ALLOWED_CAPTURE_METHODS:
            raise MobileCaptureError("拍照方式无效。", 400, "INVALID_CAPTURE_METHOD")
        facing_mode = self._text(fields, "facing_mode", 32) or "unknown"
        if facing_mode not in ALLOWED_FACING_MODES:
            raise MobileCaptureError("摄像头朝向元数据无效。", 400, "INVALID_FACING_MODE")
        width = self._dimension(fields, "width")
        height = self._dimension(fields, "height")
        declared_mime = self._text(fields, "mime_type", 32, required=True).lower()
        part_mime = (file_mime_type or declared_mime).strip().lower()
        if declared_mime not in MIME_SUFFIXES or part_mime not in MIME_SUFFIXES:
            raise MobileCaptureError("只支持 JPEG 或 PNG 图片。", 415, "UNSUPPORTED_MIME")
        if declared_mime != part_mime:
            raise MobileCaptureError("图片 MIME 声明不一致。", 415, "MIME_MISMATCH")
        suffix = Path(filename).suffix.lower()
        if suffix not in MIME_SUFFIXES[declared_mime]:
            raise MobileCaptureError("图片后缀与 MIME 不一致。", 415, "EXTENSION_MISMATCH")
        if not self._signature_matches(content, declared_mime):
            raise MobileCaptureError("图片文件签名无效。", 415, "INVALID_IMAGE_SIGNATURE")
        return MobileCaptureMetadata(
            client_capture_id=client_capture_id,
            captured_at=captured_at,
            capture_method=capture_method,
            device_label=self._text(fields, "device_label", 200),
            device_id=self._text(fields, "device_id", 200),
            facing_mode=facing_mode,
            width=width,
            height=height,
            mime_type=declared_mime,
        )

    @staticmethod
    def _text(
        fields: Mapping[str, str],
        name: str,
        maximum: int,
        required: bool = False,
    ) -> str:
        value = str(fields.get(name, "")).strip()
        if required and not value:
            raise MobileCaptureError(f"缺少字段：{name}。", 400, "MISSING_FIELD")
        if len(value) > maximum or any(ord(character) < 32 for character in value):
            raise MobileCaptureError(f"字段 {name} 超出限制。", 400, "INVALID_METADATA")
        return value

    @staticmethod
    def _dimension(fields: Mapping[str, str], name: str) -> int:
        try:
            value = int(str(fields.get(name, "")))
        except ValueError as exc:
            raise MobileCaptureError(
                f"字段 {name} 必须是整数。",
                400,
                "INVALID_DIMENSION",
            ) from exc
        if not 1 <= value <= 16384:
            raise MobileCaptureError(f"字段 {name} 超出范围。", 400, "INVALID_DIMENSION")
        return value

    @staticmethod
    def _signature_matches(content: bytes, mime_type: str) -> bool:
        if mime_type == "image/jpeg":
            return content.startswith(b"\xff\xd8\xff")
        return content.startswith(b"\x89PNG\r\n\x1a\n")
