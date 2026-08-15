"""classifier.py — trains, saves, loads and uses the Naive Bayes category model."""
import joblib
import pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report

MODEL_PATH = Path(__file__).parent / "category_model.joblib"
CSV_PATH = Path(__file__).parent.parent.parent / "data" / "refound_dataset.csv"


def train():
    df = pd.read_csv(CSV_PATH)
    X_train, X_test, y_train, y_test = train_test_split(
        df.description, df.category, test_size=0.2,
        random_state=42, stratify=df.category)

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english")),
        ("nb", MultinomialNB()),
    ])
    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, preds):.1%}")
    print(f"Macro F1: {f1_score(y_test, preds, average='macro'):.3f}")
    print(classification_report(y_test, preds))

    joblib.dump(pipe, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


def load_model():
    return joblib.load(MODEL_PATH)


def suggest_category(model, description):
    """Returns (predicted_category, confidence 0-1)."""
    pred = model.predict([description])[0]
    conf = max(model.predict_proba([description])[0])
    return pred, round(float(conf), 3)


if __name__ == "__main__":
    train()