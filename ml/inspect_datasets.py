from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "datasets" / "raw").rglob("*"):
    if path.is_file() and path.suffix.lower() in {".csv", ".tsv"}:
        try:
            df = pd.read_csv(path, sep=None, engine="python", nrows=5)
            print(f"\n{path}\ncolumns={list(df.columns)}\npreview:\n{df.head(3)}")
        except Exception as exc:
            print(f"Could not preview {path}: {exc}")
