"""Extract policy-driven mark features from one option-cell crop."""

from dataclasses import dataclass

from .cell_preprocessor import binary_mask
from .omr_policy import DEFAULT_OMR_POLICY, OMRPolicy


@dataclass(frozen=True)
class MarkMetrics:
    option: str
    dark_ratio: float
    center_density: float
    largest_component_ratio: float
    border_noise: float
    fill_uniformity: float
    erasure_score: float
    mark_score: float
    classification: str


def _largest_component_ratio(mask, width, height):
    seen = set()
    largest = 0
    for index, marked in enumerate(mask):
        if not marked or index in seen:
            continue
        stack = [index]
        seen.add(index)
        size = 0
        while stack:
            current = stack.pop()
            size += 1
            x, y = current % width, current // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                neighbor = ny * width + nx
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and mask[neighbor]
                    and neighbor not in seen
                ):
                    seen.add(neighbor)
                    stack.append(neighbor)
        largest = max(largest, size)
    return largest / len(mask)


def extract_mark_metrics(image, option, policy: OMRPolicy = DEFAULT_OMR_POLICY):
    mask = binary_mask(image, policy.dark_pixel_cutoff)
    width, height = image.width, image.height
    dark_ratio = sum(mask) / len(mask)

    x0, x1 = width // 4, (3 * width) // 4
    y0, y1 = height // 4, (3 * height) // 4
    center = [mask[y * width + x] for y in range(y0, y1) for x in range(x0, x1)]
    center_density = sum(center) / len(center)
    border = [
        mask[y * width + x]
        for y in range(height)
        for x in range(width)
        if x in (0, width - 1) or y in (0, height - 1)
    ]
    border_noise = sum(border) / len(border)

    quadrant_densities = []
    for ya, yb in ((0, height // 2), (height // 2, height)):
        for xa, xb in ((0, width // 2), (width // 2, width)):
            quadrant = [
                mask[y * width + x] for y in range(ya, yb) for x in range(xa, xb)
            ]
            quadrant_densities.append(sum(quadrant) / len(quadrant))
    fill_uniformity = max(0.0, 1.0 - (max(quadrant_densities) - min(quadrant_densities)))
    component_ratio = _largest_component_ratio(mask, width, height)
    transition_count = sum(
        mask[y * width + x] != mask[y * width + x - 1]
        for y in range(height)
        for x in range(1, width)
    )
    transition_ratio = transition_count / (height * max(1, width - 1))
    erasure_score = transition_ratio if dark_ratio > policy.weak_dark_ratio else 0.0
    mark_score = max(
        0.0,
        min(
            1.0,
            policy.dark_ratio_weight * dark_ratio
            + policy.center_density_weight * center_density
            + policy.component_weight * component_ratio
            - policy.border_noise_weight * border_noise,
        ),
    )

    if border_noise > policy.border_noise_limit and center_density < policy.weak_dark_ratio:
        classification = "dirty"
    elif erasure_score > policy.erasure_threshold and dark_ratio < policy.strong_dark_ratio:
        classification = "erased"
    elif dark_ratio >= policy.strong_dark_ratio and center_density >= policy.strong_center_density:
        classification = "strong"
    elif dark_ratio >= policy.weak_dark_ratio:
        classification = "weak"
    else:
        classification = "blank"
    return MarkMetrics(
        option, dark_ratio, center_density, component_ratio, border_noise,
        fill_uniformity, erasure_score, mark_score, classification,
    )
