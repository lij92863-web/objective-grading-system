"""Camera device contract (constitution §5).

The ONLY supported capture source is the browser ``getUserMedia()`` /
``enumerateDevices()`` API. USB phone tethering, ADB, and iOS native camera
access are explicitly forbidden. This module provides the contract constants
and a validation function used by the capture layer before any bytes are stored.
"""

from typing import Iterable


SOURCE_BROWSER = "browser"

# Explicitly forbidden capture sources (constitution §5.2).
FORBIDDEN_SOURCES = frozenset(
    {
        "usb_phone",
        "usb",
        "adb",
        "android_adb",
        "ios_native",
        "ios",
        "avfoundation",
        "mtp",
        "ptp",
        "device_mount",
        "filesystem_direct",
    }
)

SUPPORTED_SOURCES = frozenset({SOURCE_BROWSER})


class UnsupportedCaptureSourceError(ValueError):
    """Raised when a capture source violates the device contract."""


def is_supported_source(source) -> bool:
    if not isinstance(source, str) or not source:
        return False
    return source in SUPPORTED_SOURCES and source not in FORBIDDEN_SOURCES


def assert_supported_source(source) -> str:
    if not is_supported_source(source):
        raise UnsupportedCaptureSourceError(
            f"capture source {source!r} is not allowed; only browser "
            f"getUserMedia()/enumerateDevices() is supported"
        )
    return source


def contract_summary() -> str:
    return (
        "Only browser navigator.mediaDevices.getUserMedia()/enumerateDevices() "
        "is supported. USB phone tethering, ADB and iOS native camera are forbidden."
    )
