from pathlib import Path
import json
import sys

import joblib
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "backend"))

from app.unicode_tokenizer import unicode_tokenizer

DATA_DIR = ROOT / "datasets" / "processed" / "bsis_single_message"
MODEL_DIR = ROOT / "ml" / "models"
METRICS_DIR = ROOT / "datasets" / "interim"

TRAIN_FILE = DATA_DIR / "train_clean.csv"
VALIDATION_FILE = DATA_DIR / "validation.csv"

# Separate experimental artifacts. Existing models remain untouched.
MODEL_FILE = MODEL_DIR / "bsis_single_message_unicode_experimental.joblib"
METRICS_FILE = METRICS_DIR / "bsis_single_message_unicode_experimental.json"

TARGET_FPR = 0.10
THRESHOLDS = np.round(np.arange(0.50, 0.951, 0.01), 2)





def calculate_metrics(y_true, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true, predictions, labels=[0, 1]
    ).ravel()

    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(
            precision_score(y_true, predictions, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, predictions, zero_division=0)
        ),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def select_threshold(y_true, probabilities):
    results = [
        calculate_metrics(y_true, probabilities, threshold)
        for threshold in THRESHOLDS
    ]

    eligible = [
        item for item in results
        if item["false_positive_rate"] <= TARGET_FPR
    ]

    if not eligible:
        selected = min(
            results,
            key=lambda item: (
                item["false_positive_rate"],
                -item["recall"],
            ),
        )
        return selected["threshold"], False, results

    selected = max(
        eligible,
        key=lambda item: (
            item["recall"],
            item["precision"],
            item["f1"],
        ),
    )

    return selected["threshold"], True, results


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading single-message datasets...")

    train = pd.read_csv(TRAIN_FILE)
    validation = pd.read_csv(VALIDATION_FILE)

    required = {"text", "label", "language", "script_mode"}

    for name, frame in [
        ("training", train),
        ("validation", validation),
    ]:
        missing = required - set(frame.columns)

        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")

        if frame[list(required)].isna().any().any():
            raise ValueError(f"{name} contains missing required values.")

        if not set(frame["label"].unique()).issubset({0, 1}):
            raise ValueError(f"{name} has unexpected labels.")

    print("Training rows:", len(train))
    print("Validation rows:", len(validation))

    features = FeatureUnion([
        (
            "unicode_word_tfidf",
            TfidfVectorizer(
                analyzer="word",
                tokenizer=unicode_tokenizer,
                token_pattern=None,
                ngram_range=(1, 2),
                max_features=100000,
                min_df=2,
                sublinear_tf=True,
            ),
        ),
        (
            "char_tfidf",
            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(2, 5),
                max_features=150000,
                min_df=2,
                sublinear_tf=True,
            ),
        ),
    ])

    model = Pipeline([
        ("features", features),
        (
            "classifier",
            LogisticRegression(
                max_iter=300,
                class_weight="balanced",
                solver="liblinear",
                random_state=42,
            ),
        ),
    ])

    print("\nTraining Unicode-aware experimental model...")
    model.fit(train["text"], train["label"])

    print("Training completed.")

    y_true = validation["label"].to_numpy()
    probabilities = model.predict_proba(validation["text"])[:, 1]

    threshold, target_met, threshold_results = select_threshold(
        y_true, probabilities
    )

    overall = calculate_metrics(y_true, probabilities, threshold)

    language_metrics = {}
    script_metrics = {}

    for language, group in validation.groupby("language"):
        positions = validation.index.get_indexer(group.index)

        language_metrics[language] = calculate_metrics(
            group["label"].to_numpy(),
            probabilities[positions],
            threshold,
        )

    kn = validation["language"].eq("kn-IN")

    for script_mode, group in validation[kn].groupby("script_mode"):
        positions = validation.index.get_indexer(group.index)

        script_metrics[script_mode] = calculate_metrics(
            group["label"].to_numpy(),
            probabilities[positions],
            threshold,
        )

    report = {
        "model": "BSIS single-message Unicode-aware experimental TF-IDF",
        "training_rows": len(train),
        "validation_rows": len(validation),
        "tokenizer": "NFC normalization and Unicode letter/mark preservation",
        "features": {
            "word_ngrams": "1-2",
            "character_ngrams": "2-5",
            "word_max_features": 100000,
            "character_max_features": 150000,
        },
        "threshold_selection": {
            "method": "Highest recall subject to validation FPR constraint",
            "target_fpr": TARGET_FPR,
            "target_achieved": target_met,
            "candidate_thresholds": THRESHOLDS.tolist(),
        },
        "selected_threshold": threshold,
        "validation_metrics": overall,
        "threshold_comparison": threshold_results,
        "language_metrics": language_metrics,
        "kannada_script_metrics": script_metrics,
        "test_set_used": False,
    }

    joblib.dump(model, MODEL_FILE)

    with METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n========== EXPERIMENTAL VALIDATION RESULTS ==========")

    for metric, value in overall.items():
        print(f"{metric}: {value}")

    print("\nKannada script metrics:")

    for script, metrics in script_metrics.items():
        print(script, metrics)

    print("\nSelected threshold:", threshold)
    print("Validation FPR target achieved:", target_met)
    print("Model saved:", MODEL_FILE)
    print("Metrics saved:", METRICS_FILE)
    print("Independent test set was NOT used.")


if __name__ == "__main__":
    main()
