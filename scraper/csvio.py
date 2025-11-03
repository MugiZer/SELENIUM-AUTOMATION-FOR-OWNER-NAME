import datetime as dt
from pathlib import Path
from typing import Dict

import pandas as pd

from .schema import OUTPUT_COLUMNS, attach_normalized_borough


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def write_csv(path: Path, df: pd.DataFrame) -> Path:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp_path, index=False)
    tmp_path.replace(path)
    return path


def export_snapshot(df: pd.DataFrame, exports_dir: Path) -> Path:
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M")
    snapshot_path = exports_dir / f"enriched_{timestamp}.csv"
    df.to_csv(snapshot_path, index=False)
    return snapshot_path


def backup_original(path: Path, df: pd.DataFrame) -> Path:
    timestamp = dt.datetime.utcnow().strftime("%Y%m%d_%H%M")
    backup_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
    df.to_csv(backup_path, index=False)
    return backup_path


def ensure_output_columns(row: Dict[str, str]) -> Dict[str, str]:
    for col in OUTPUT_COLUMNS:
        row.setdefault(col, "")
    return attach_normalized_borough(row)
