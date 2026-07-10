import dataclasses


@dataclasses.dataclass(frozen=True)
class CameraProbeResult:
    available: bool
    message: str


def probe_system_camera() -> CameraProbeResult:
    return CameraProbeResult(
        False,
        "后端不直接枚举摄像头；请在浏览器页面检查系统可见设备。",
    )
