from dataclasses import dataclass
@dataclass(frozen=True)
class BenchmarkCase: sheet_id:str; perturbation:str; image_path:str; ground_truth_path:str
