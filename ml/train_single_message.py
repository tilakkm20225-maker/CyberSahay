
from pathlib import Path
import json

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

DATA_DIR = ROOT / "datasets" / "processed" / "bsis_single_message"
MODEL_DIR = ROOT / "ml" / "models"
METRICS_DIR = ROOT / "datasets" / "interim"

TRAIN_FILE = DATA_DIR / "train_clean.csv"
VALIDATION_FILE = DATA_DIR / "validation.csv"

# Separate artifacts: original baseline remains untouched.
MODEL_FILE = MODEL_DIR / "bsis_single_message_fpr_controlled.joblib"
METRICS_FILE = METRICS_DIR / "bsis_single_message_fpr_controlled_metrics.json"

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
    results = []

    for threshold in THRESHOLDS:
        metrics = calculate_metrics(
            y_true, probabilities, threshold
        )
        results.append(metrics)

    eligible = [
        item for item in results
        if item["false_positive_rate"] <= TARGET_FPR
    ]

    if eligible:
        selected = max(
            eligible,
            key=lambda item: (
                item["recall"],
                item["precision"],
                item["f1"],
            ),
        )
        target_met = True
    else:
        selected = min(
            results,
            key=lambda item: (
                item["false_positive_rate"],
                -item["recall"],
            ),
        )
        target_met = False

    return selected["threshold"], target_met, results


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading prepared single-message datasets...")

    train = pd.read_csv(TRAIN_FILE)
    validation = pd.read_csv(VALIDATION_FILE)

    required_columns = {"text", "label", "language"}

    for name, frame in [
        ("training", train),
        ("validation", validation),
    ]:
        missing = required_columns - set(frame.columns)

        if missing:
            raise ValueError(
                f"{name} dataset is missing columns: {sorted(missing)}"
            )

        if frame[list(required_columns)].isna().any().any():
            raise ValueError(
                f"{name} dataset contains missing required values."
            )

        if not set(frame["label"].unique()).issubset({0, 1}):
            raise ValueError(f"{name} dataset has unexpected labels.")

    print("Training rows:", len(train))
    print("Validation rows:", len(validation))
    print("Training languages:", train["language"].nunique())
    print("Validation languages:", validation["language"].nunique())

    print("\nBuilding word + character TF-IDF model...")

    features = FeatureUnion([
        (
            "word_tfidf",
            TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                max_features=100000,
                min_df=2,
                sublinear_tf=True,
                strip_accents=None,
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
                strip_accents=None,
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

    print("\nTraining model...")
    model.fit(train["text"], train["label"])
    print("Training completed.")

    print("\nGenerating validation scores...")
    probabilities = model.predict_proba(validation["text"])[:, 1]
    y_true = validation["label"].to_numpy()

    threshold, target_met, threshold_results = select_threshold(
        y_true, probabilities
    )

    overall_metrics = calculate_metrics(
        y_true, probabilities, threshold
    )

    print("\n========== THRESHOLD COMPARISON ==========")
    print("Target FPR:", TARGET_FPR)

    print(
        f"{'Threshold':<12}"
        f"{'Precision':<12}"
        f"{'Recall':<12}"
        f"{'F1':<12}"
        f"{'FPR':<12}"
    )

    for item in threshold_results:
        print(
            f"{item['threshold']:<12.2f}"
            f"{item['precision']:<12.3f}"
            f"{item['recall']:<12.3f}"
            f"{item['f1']:<12.3f}"
            f"{item['false_positive_rate']:<12.3f}"
        )

    print("\nSelected threshold:", threshold)
    print("FPR target achieved:", target_met)

    # Language-wise evaluation using the same global threshold.
    language_metrics = {}

    languages = validation["language"].to_numpy()

    for language in sorted(validation["language"].unique()):
        positions = np.flatnonzero(languages == language)

        language_metrics[language] = calculate_metrics(
            y_true[positions],
            probabilities[positions],
            threshold,
        )

    report = {
        "model": "BSIS single-message FPR-controlled TF-IDF Logistic Regression",
        "training_rows": len(train),
        "validation_rows": len(validation),
        "training_languages": int(train["language"].nunique()),
        "validation_languages": int(validation["language"].nunique()),
        "features": {
            "word_ngrams": "1-2",
            "character_ngrams": "2-5",
            "word_max_features": 100000,
            "character_max_features": 150000,
        },
        "classifier": {
            "type": "LogisticRegression",
            "class_weight": "balanced",
            "max_iter": 300,
            "solver": "liblinear",
        },
        "threshold_selection": {
            "method": "Highest recall subject to validation FPR constraint",
            "target_fpr": TARGET_FPR,
            "candidate_thresholds": THRESHOLDS.tolist(),
            "target_achieved": target_met,
        },
        "selected_threshold": threshold,
        "validation_metrics": overall_metrics,
        "threshold_comparison": threshold_results,
        "language_metrics": language_metrics,
        "test_set_used": False,
    }

    print("\nSaving improved model...")
    joblib.dump(model, MODEL_FILE)

    with METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n========== FINAL VALIDATION RESULTS ==========")

    for metric, value in overall_metrics.items():
        print(f"{metric}: {value}")

    print("\n========== LANGUAGE-WISE F1 ==========")

    for language, metrics in language_metrics.items():
        print(f"{language}: {metrics['f1']:.4f}")

    print("\nModel saved:", MODEL_FILE)
    print("Metrics saved:", METRICS_FILE)

    print("\nTest dataset was NOT used.")
    print("FPR-controlled training completed.")


if __name__ == "__main__":
    main()
