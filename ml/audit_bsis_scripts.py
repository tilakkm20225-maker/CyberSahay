
from pathlib import Path
from collections import Counter, defaultdict
import unicodedata
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "datasets" / "processed" / "bsis_v1"
OUTPUT_DIR = ROOT / "datasets" / "interim"

SCRIPT_MARKERS = [
    "LATIN",
    "DEVANAGARI",
    "BENGALI",
    "GURMUKHI",
    "GUJARATI",
    "ORIYA",
    "TAMIL",
    "TELUGU",
    "KANNADA",
    "MALAYALAM",
    "ARABIC",
    "CJK",
    "HIRAGANA",
    "KATAKANA",
    "HANGUL",
    "THAI",
    "MYANMAR",
    "TIBETAN",
    "CYRILLIC",
    "GREEK",
]


def detect_script(character):
    name = unicodedata.name(character, "")

    for marker in SCRIPT_MARKERS:
        if marker in name:
            return marker

    return None


def main():
    script_counts = defaultdict(Counter)
    mixed_script_rows = defaultdict(list)
    split_sizes = {}

    for split in ["train_clean", "validation", "test"]:
        path = DATA_DIR / f"{split}.csv"
        df = pd.read_csv(path)

        split_sizes[split] = len(df)

        for _, row in df.iterrows():
            text = str(row["text"])
            language = row["language"]

            scripts = Counter(
                detect_script(char)
                for char in text
                if detect_script(char) is not None
            )

            for script, count in scripts.items():
                script_counts[language][script] += count

            if len(scripts) > 1:
                if len(mixed_script_rows[language]) < 5:
                    mixed_script_rows[language].append({
                        "split": split,
                        "scripts": dict(scripts),
                        "text": text[:500],
                    })

    report = {
        "split_sizes": split_sizes,
        "scripts_by_language": {
            lang: dict(counts.most_common())
            for lang, counts in sorted(script_counts.items())
        },
        "mixed_script_examples": dict(mixed_script_rows),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output = OUTPUT_DIR / "bsis_script_audit.json"

    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("========== BSIS SCRIPT AUDIT ==========")

    for language, counts in sorted(script_counts.items()):
        print(f"\n{language}:")
        for script, count in counts.most_common():
            print(f"  {script}: {count}")

    print("\nMixed-script examples collected:")
    print(sum(len(v) for v in mixed_script_rows.values()))

    print("\nReport saved:", output)


if __name__ == "__main__":
    main()
