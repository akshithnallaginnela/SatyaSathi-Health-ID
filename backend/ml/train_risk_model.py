from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

VALID_LABELS = {"low", "moderate", "high"}


def load_dataset(dataset_path: Path) -> tuple[pd.Series, pd.Series]:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    required_columns = {"text", "label"}
    if not required_columns.issubset(df.columns):
        raise ValueError("Dataset must contain 'text' and 'label' columns")

    df = df.dropna(subset=["text", "label"]).copy()
    df["label"] = df["label"].astype(str).str.strip().str.lower()
    df["text"] = df["text"].astype(str).str.strip()

    df = df[df["label"].isin(VALID_LABELS)]
    if df.empty:
        raise ValueError("No valid rows found. Allowed labels: low, moderate, high")

    return df["text"], df["label"]


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    max_features=8000,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    multi_class="auto",
                ),
            ),
        ]
    )


def train_and_evaluate(dataset_path: Path, output_path: Path, test_size: float, random_state: int) -> None:
    X, y = load_dataset(dataset_path)

    class_counts = y.value_counts()
    can_stratify = bool((class_counts >= 2).all()) and len(X) > 10

    if can_stratify:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=y,
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=min(0.2, test_size),
            random_state=random_state,
        )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    artifact = {
        "pipeline": pipeline,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "accuracy": round(float(accuracy), 4),
            "samples": int(len(X)),
            "test_samples": int(len(X_test)),
            "labels": sorted(list(set(y.tolist()))),
            "classification_report": report,
        },
        "dataset_path": str(dataset_path),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, output_path)

    print("Training completed")
    print(f"Model saved to: {output_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Samples: {len(X)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train health risk text classifier")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("ml/training_data/sample_health_risk_data.csv"),
        help="Path to CSV dataset with columns: text,label",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/models/risk_model.joblib"),
        help="Path to save model artifact",
    )
    parser.add_argument("--test-size", type=float, default=0.25, help="Holdout ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_and_evaluate(
        dataset_path=args.dataset,
        output_path=args.output,
        test_size=args.test_size,
        random_state=args.seed,
    )


if __name__ == "__main__":
    main()
