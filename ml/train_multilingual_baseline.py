
from pathlib import Path
import json

import joblib
import pandas as pd
import numpy as np

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

DATA_DIR = ROOT / "datasets" / "processed" / "bsis_v1"
MODEL_DIR = ROOT / "ml" / "models"
METRICS_DIR = ROOT / "datasets" / "interim"

TRAIN_FILE = DATA_DIR / "train_clean.csv"
VALIDATION_FILE = DATA_DIR / "validation.csv"

MODEL_FILE = MODEL_DIR / "bsis_multilingual_fpr_controlled.joblib"
METRICS_FILE = METRICS_DIR / "bsis_multilingual_fpr_controlled_metrics.json"

FPR_TARGET = 0.10


def calculate_metrics(y_true, probabilities, threshold):
    predictions = (probabilities >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true, predictions, labels=[0, 1]
    ).ravel()

    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1": float(f1_score(y_true, predictions, zero_division=0)),
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else 0.0,
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
    }


def select_threshold(y_true, probabilities):
    candidates = np.unique(probabilities)
    eligible = []

    for threshold in candidates:
        metrics = calculate_metrics(y_true, probabilities, threshold)

        if metrics["false_positive_rate"] <= FPR_TARGET:
            eligible.append((float(threshold), metrics))

    if not eligible:
        raise RuntimeError(
            "No validation threshold satisfies the FPR target."
        )

    # Highest recall first; precision breaks ties.
    return max(
        eligible,
        key=lambda item: (
            item[1]["recall"],
            item[1]["precision"],
        ),
    )


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading full-conversation BSIS datasets...")

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

    print("\nTraining conversation model...")
    model.fit(train["text"], train["label"])
    print("Training completed.")

    print("\nEvaluating validation data...")

    y_true = validation["label"].to_numpy()
    probabilities = model.predict_proba(validation["text"])[:, 1]

    threshold, overall_metrics = select_threshold(
        y_true, probabilities
    )

    language_metrics = {}

    for language, group in validation.groupby("language"):
        positions = validation.index.get_indexer(group.index)

        language_metrics[language] = calculate_metrics(
            group["label"].to_numpy(),
            probabilities[positions],
            threshold,
        )

    report = {
        "model": "BSIS full-conversation multilingual TF-IDF Logistic Regression",
        "input_type": "Full conversation window",
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
        "threshold_selection": (
            "Highest validation recall subject to validation FPR <= 0.10; "
            "precision breaks ties"
        ),
        "fpr_target": FPR_TARGET,
        "selected_threshold": threshold,
        "validation_metrics": overall_metrics,
        "language_metrics": language_metrics,
        "test_set_used": False,
    }

    print("\nSaving separate model and metrics...")
    joblib.dump(model, MODEL_FILE)

    with METRICS_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n========== VALIDATION RESULTS ==========")
    print(f"Selected threshold: {threshold:.8f}")

    for metric, value in overall_metrics.items():
        print(f"{metric}: {value}")

    print("\n========== LANGUAGE-WISE F1 ==========")

    for language, metrics in sorted(language_metrics.items()):
        print(f"{language}: {metrics['f1']:.4f}")

    print("\nModel saved:", MODEL_FILE)
    print("Metrics saved:", METRICS_FILE)
    print("\nTest dataset was NOT used.")
    print("FPR-controlled conversation training completed.")


if __name__ == "__main__":
    main()
