from dataclasses import dataclass

@dataclass(frozen=True)
class PageLocatorPolicy:
    min_variance: float = 4.0
    max_aspect_ratio_error: float = 0.25

DEFAULT_PAGE_LOCATOR_POLICY = PageLocatorPolicy()
