
from pathlib import Path
import json
import sys

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

MODELS = [
    {
        "name": "Single-message",
        "model": ROOT / "ml/models/bsis_single_message_fpr_controlled.joblib",
        "test": ROOT / "datasets/processed/bsis_single_message/test.csv",
        "threshold": 0.7236015808024677,
    },
    {
        "name": "Single-message Unicode experimental",
        "model": ROOT / "ml/models/bsis_single_message_unicode_experimental.joblib",
        "test": ROOT / "datasets/processed/bsis_single_message/test.csv",
        "threshold": 0.73,
    },
    {
        "name": "Full-conversation",
        "model": ROOT / "ml/models/bsis_multilingual_fpr_controlled.joblib",
        "test": ROOT / "datasets/processed/bsis_v1/test.csv",
        "threshold": 0.74818514,
    },
]

OUTPUT = ROOT / "datasets/interim/unicode_experimental_test_evaluation.json"


def evaluate(config):
    print(f"\nEvaluating {config['name']} model...")

    model = joblib.load(config["model"])
    data = pd.read_csv(config["test"])

    y_true = data["label"].to_numpy()
    probabilities = model.predict_proba(data["text"])[:, 1]
    predictions = (probabilities >= config["threshold"]).astype(int)

    tn, fp, fn, tp = confusion_matrix(
        y_true, predictions, labels=[0, 1]
    ).ravel()

    metrics = {
        "test_rows": len(data),
        "threshold": config["threshold"],
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

    language_metrics = {}

    for language, group in data.groupby("language"):
        positions = data.index.get_indexer(group.index)

        group_predictions = predictions[positions]

        language_metrics[language] = {
            "rows": len(group),
            "precision": float(precision_score(
                group["label"], group_predictions, zero_division=0
            )),
            "recall": float(recall_score(
                group["label"], group_predictions, zero_division=0
            )),
            "f1": float(f1_score(
                group["label"], group_predictions, zero_division=0
            )),
        }

    print("\nOverall test metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print("\nLanguage-wise F1:")
    for language, result in sorted(language_metrics.items()):
        print(f"{language}: {result['f1']:.4f} (n={result['rows']})")

    return {
        "model": config["name"],
        "metrics": metrics,
        "language_metrics": language_metrics,
    }


def main():
    results = []

    for config in MODELS:
        results.append(evaluate(config))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    print("\nFinal independent test evaluation completed.")
    print("Report saved:", OUTPUT)
    print("No thresholds were tuned on the test data.")


if __name__ == "__main__":
    main()
