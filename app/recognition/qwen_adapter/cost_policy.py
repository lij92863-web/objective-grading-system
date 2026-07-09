"""R97: Qwen cost policy model."""
from dataclasses import dataclass


@dataclass
class QwenCostPolicy:
    estimated_calls: int = 0
    max_calls_per_batch: int = 10
    max_calls_per_image: int = 3
    estimated_cost_units: float = 0.0
    cost_per_call: float = 0.002

    def status(self) -> str:
        if self.max_calls_per_batch == 0: return "disabled"
        ratio = self.estimated_calls / self.max_calls_per_batch if self.max_calls_per_batch else 999
        if ratio > 1.0: return "exceeds_limit"
        if ratio > 0.8: return "near_limit"
        return "within_limit"

    def compute(self):
        self.estimated_cost_units = self.estimated_calls * self.cost_per_call
