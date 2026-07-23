from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MLConfig:
    """Configuration values for the ML package."""

    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = project_root / "ml" / "data"
    models_dir: Path = project_root / "ml" / "models"
    mock_model_path: Path = project_root / "ml" / "models" / "mock_model.pkl"


CONFIG = MLConfig()
