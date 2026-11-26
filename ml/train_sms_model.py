
from pathlib import Path
import csv
import json
from datetime import datetime, timezone

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "datasets" / "interim" / "uci_sms_spam_deduplicated.tsv"
MODEL_DIR = ROOT / "ml" / "models"
METRICS_DIR = ROOT / "datasets" / "interim"

MODEL_PATH = MODEL_DIR / "sms_model.joblib"
METRICS_PATH = METRICS_DIR / "uci_sms_model_metrics.json"

LABELS = ["ham", "spam"]


def load_data():
    if not DATA.exists():
        raise FileNotFoundError(
            f"Cleaned UCI dataset not found: {DATA}"
        )

    df = pd.read_csv(
        DATA,
        sep="\t",
        header=None,
        names=["label", "text"],
        encoding="utf-8",
        quoting=csv.QUOTE_NONE,
        on_bad_lines="error",
    )

    df = df.dropna(subset=["text", "label"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.lower().str.strip()

    df = df[
        df["label"].isin(LABELS)
        & (df["text"] != "")
    ].copy()

    if df["label"].nunique() != 2:
        raise ValueError("Expected both ham and spam labels.")

    print("\nDataset summary")
    print("----------------")
    print("Total messages:", len(df))
    print("\nLabel distribution:")
    print(df["label"].value_counts())

    return df


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"],
        df["label"],
        test_size=0.20,
        random_state=42,
        stratify=df["label"],
    )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                strip_accents="unicode",
                min_df=2,
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

    print("\nTraining English SMS baseline...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=LABELS,
    )

    tn, fp, fn, tp = matrix.ravel()

    metrics = {
        "dataset": "UCI SMS Spam Collection",
        "language": "English",
        "total_records": len(df),
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision_spam": float(
            precision_score(
                y_test, predictions,
                pos_label="spam",
                zero_division=0,
            )
        ),
        "recall_spam": float(
            recall_score(
                y_test, predictions,
                pos_label="spam",
                zero_division=0,
            )
        ),
        "f1_spam": float(
            f1_score(
                y_test, predictions,
                pos_label="spam",
                zero_division=0,
            )
        ),
        "false_positive_rate": (
            float(fp / (fp + tn)) if (fp + tn) else None
        ),
        "false_negative_rate": (
            float(fn / (fn + tp)) if (fn + tp) else None
        ),
        "confusion_matrix": {
            "labels": LABELS,
            "values": matrix.tolist(),
        },
        "classification_report": classification_report(
            y_test,
            predictions,
            labels=LABELS,
            output_dict=True,
            zero_division=0,
        ),
        "evaluation_type": "stratified random holdout",
        "random_state": 42,
        "evaluated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    joblib.dump(model, MODEL_PATH)

    METRICS_PATH.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )

    print("\nEvaluation results")
    print("------------------")
    print(classification_report(
        y_test,
        predictions,
        labels=LABELS,
        zero_division=0,
    ))

    print("Confusion matrix:")
    print(matrix)

    print("\nFalse positive rate:", metrics["false_positive_rate"])
    print("False negative rate:", metrics["false_negative_rate"])

    print("\nModel saved:", MODEL_PATH)
    print("Metrics saved:", METRICS_PATH)
    print("\nEnglish baseline training completed.")


if __name__ == "__main__":
    main()
