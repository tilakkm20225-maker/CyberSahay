from pathlib import Path
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "demo_sms.csv"
OUT = ROOT / "ml" / "models"
OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA).dropna(subset=["text", "label"])
df["text"] = df["text"].astype(str).str.strip()
df["label"] = df["label"].astype(str).str.lower().str.strip()
df = df[df.label.isin(["spam", "ham"])].drop_duplicates("text")
X_train, X_test, y_train, y_test = train_test_split(
    df.text, df.label, test_size=0.25, random_state=42, stratify=df.label
)
model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
    ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced"))
])
model.fit(X_train, y_train)
print(classification_report(y_test, model.predict(X_test), zero_division=0))
joblib.dump(model, OUT / "sms_model.joblib")
print(f"Saved model: {OUT / 'sms_model.joblib'}")
