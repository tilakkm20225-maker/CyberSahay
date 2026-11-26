
from pathlib import Path
import argparse
import json

import pandas as pd
from datasets import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "processed" / "bsis_v1"

REQUIRED_COLUMNS = {
    "text",
    "label",
    "language",
    "script_mode",
    "vector",
    "round",
    "lineage_id",
    "hard_example",
}


def main():
    parser = argparse.ArgumentParser(
        description="Prepare and audit the BSIS multilingual dataset."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing previously generated output files.",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_files = [
        OUTPUT_DIR / "train_clean.csv",
        OUTPUT_DIR / "validation.csv",
        OUTPUT_DIR / "test.csv",
        OUTPUT_DIR / "audit_report.json",
    ]

    if not args.overwrite:
        existing = [str(path) for path in output_files if path.exists()]
        if existing:
            raise SystemExit(
                "Output files already exist. Use --overwrite to replace them."
            )

    print("Loading BSIS dataset...")
    dataset = load_dataset("harshcasper/bsis", "classifier")

    frames = {
        split: pd.DataFrame(dataset[split])
        for split in ("train", "validation", "test")
    }

    for split, df in frames.items():
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"{split} is missing columns: {sorted(missing)}")

        if df["text"].isna().any():
            raise ValueError(f"{split} contains missing message text.")

    train = frames["train"].copy()

    # Identify exact message texts with more than one label.
    label_counts = train.groupby("text")["label"].nunique()
    conflicting_texts = set(label_counts[label_counts > 1].index)

    conflicting_rows = train["text"].isin(conflicting_texts)
    conflict_group_count = len(conflicting_texts)
    conflict_row_count = int(conflicting_rows.sum())

    # Remove every row belonging to a conflicting exact-text group.
    train_without_conflicts = train.loc[~conflicting_rows].copy()

    # Count repeated exact messages before deduplication.
    duplicate_counts = train_without_conflicts["text"].value_counts()
    repeated_groups = duplicate_counts[duplicate_counts > 1]

    extra_duplicate_rows = int((repeated_groups - 1).sum())

    # Keep the first occurrence of each exact message.
    train_clean = train_without_conflicts.drop_duplicates(
        subset=["text"],
        keep="first",
    ).copy()

    # Measure exact text overlap between the original splits.
    overlap_counts = {}
    split_names = ("train", "validation", "test")

    for i, first in enumerate(split_names):
        for second in split_names[i + 1:]:
            overlap = set(frames[first]["text"]) & set(frames[second]["text"])
            overlap_counts[f"{first}_vs_{second}"] = len(overlap)

    audit = {
        "dataset": "harshcasper/bsis",
        "configuration": "classifier",
        "preparation_method": "exact_text_conflict_exclusion_and_deduplication",
        "original_split_sizes": {
            split: len(df) for split, df in frames.items()
        },
        "training_audit": {
            "original_rows": len(train),
            "unique_exact_messages_before_cleaning": int(
                train["text"].nunique()
            ),
            "conflicting_exact_text_groups": conflict_group_count,
            "rows_excluded_due_to_conflicting_labels": conflict_row_count,
            "rows_after_conflict_exclusion": len(train_without_conflicts),
            "repeated_groups_after_conflict_exclusion": len(repeated_groups),
            "extra_duplicate_rows_removed": extra_duplicate_rows,
            "final_training_rows": len(train_clean),
            "final_unique_training_messages": int(
                train_clean["text"].nunique()
            ),
        },
        "validation_and_test": {
            "validation_preserved_unchanged": True,
            "test_preserved_unchanged": True,
        },
        "exact_text_overlap_between_original_splits": overlap_counts,
        "cleaning_rules": [
            "Original downloaded dataset is not modified.",
            "All training rows from conflicting exact-text groups are excluded.",
            "Exact duplicate training messages are reduced to their first occurrence.",
            "Original labels and metadata of retained rows are preserved.",
            "Validation and test splits are exported unchanged.",
        ],
    }

    # Export all three splits.
    train_clean.to_csv(
        output_files[0], index=False, encoding="utf-8-sig"
    )

    frames["validation"].to_csv(
        output_files[1], index=False, encoding="utf-8-sig"
    )

    frames["test"].to_csv(
        output_files[2], index=False, encoding="utf-8-sig"
    )

    with output_files[3].open("w", encoding="utf-8") as file:
        json.dump(audit, file, indent=4, ensure_ascii=False)

    print("\n========== BSIS PREPARATION REPORT ==========")
    print("Original training rows:", len(train))
    print("Conflicting text groups:", conflict_group_count)
    print("Rows excluded for label conflicts:", conflict_row_count)
    print("Repeated groups remaining:", len(repeated_groups))
    print("Extra duplicate rows removed:", extra_duplicate_rows)
    print("Final training rows:", len(train_clean))
    print("\nExact text overlap between splits:")
    for pair, count in overlap_counts.items():
        print(f"  {pair}: {count}")

    print("\nValidation rows preserved:", len(frames["validation"]))
    print("Test rows preserved:", len(frames["test"]))
    print("\nOutput directory:", OUTPUT_DIR)
    print("Preparation completed successfully.")


if __name__ == "__main__":
    main()
