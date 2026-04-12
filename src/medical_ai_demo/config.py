from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_ROOT = Path("data/generated")


@dataclass(frozen=True)
class OutputPaths:
    root: Path
    raw_dir: Path
    analytics_dir: Path
    reports_dir: Path


def build_output_paths(root: Path | str = DEFAULT_OUTPUT_ROOT) -> OutputPaths:
    root_path = Path(root)
    return OutputPaths(
        root=root_path,
        raw_dir=root_path / "raw",
        analytics_dir=root_path / "analytics",
        reports_dir=root_path / "reports",
    )


def ensure_output_dirs(paths: OutputPaths) -> None:
    for directory in (paths.root, paths.raw_dir, paths.analytics_dir, paths.reports_dir):
        directory.mkdir(parents=True, exist_ok=True)

