
from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "datasets" / "processed" / "bsis_single_message"
OUTPUT_DIR = ROOT / "ml" / "experiments"

TRAIN_PATH = DATA_DIR / "train_clean.csv"
VALIDATION_PATH = DATA_DIR / "validation.csv"

MODEL_PATH = OUTPUT_DIR / "language_detector_experimental.joblib"
REPORT_PATH = OUTPUT_DIR / "language_detector_validation.json"

train = pd.read_csv(TRAIN_PATH)
validation = pd.read_csv(VALIDATION_PATH)

required = {"text", "language", "script_mode"}

assert required.issubset(train.columns)
assert required.issubset(validation.columns)

assert train[list(required)].notna().all().all()
assert validation[list(required)].notna().all().all()

model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            analyzer="char",
            ngram_range=(2, 5),
            min_df=2,
            max_features=250000,
            sublinear_tf=True,
        ),
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1500,
            class_weight="balanced",
            random_state=42,
        ),
    ),
])

print("Training experimental language detector...")
model.fit(train["text"].astype(str), train["language"])

predictions = model.predict(validation["text"].astype(str))

overall_accuracy = accuracy_score(
    validation["language"],
    predictions,
)

print("\nOVERALL VALIDATION ACCURACY:")
print(f"{overall_accuracy:.4f}")

print("\nOVERALL CLASSIFICATION REPORT:")
print(classification_report(
    validation["language"],
    predictions,
    zero_division=0,
))

print("\nSCRIPT MODE EVALUATION:")

script_results = {}

for script_mode, subset in validation.groupby("script_mode"):
    subset_predictions = model.predict(subset["text"].astype(str))

    accuracy = accuracy_score(
        subset["language"],
        subset_predictions,
    )

    script_results[script_mode] = {
        "samples": len(subset),
        "accuracy": float(accuracy),
        "report": classification_report(
            subset["language"],
            subset_predictions,
            output_dict=True,
            zero_division=0,
        ),
    }

    print(
        f"{script_mode}: "
        f"{accuracy:.4f} "
        f"({len(subset)} samples)"
    )

report = {
    "experiment": "experimental_character_ngram_language_detector",
    "training_samples": len(train),
    "validation_samples": len(validation),
    "language_count": int(train["language"].nunique()),
    "overall_accuracy": float(overall_accuracy),
    "script_mode_results": script_results,
    "limitations": [
        "Synthetic dataset evaluation only",
        "Validation performance is not real-world performance",
        "No probability calibration performed",
        "Romanized language confusion requires separate analysis",
    ],
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(model, MODEL_PATH)

with open(REPORT_PATH, "w", encoding="utf-8") as file:
    json.dump(report, file, indent=2)

print("\nMODEL SAVED:", MODEL_PATH)
print("REPORT SAVED:", REPORT_PATH)
print("\nEXPERIMENT COMPLETE.")
print("Existing scam detection models were not modified.")
