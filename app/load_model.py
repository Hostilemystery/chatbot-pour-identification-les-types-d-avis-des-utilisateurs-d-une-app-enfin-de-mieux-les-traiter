import joblib
import os

model_path = os.path.join(os.path.dirname(
    __file__), "..", "model", "model_bug_classifier.pkl")
vectorizer_path = os.path.join(os.path.dirname(
    __file__), "..", "model", "vectorizer_bug_classifier.pkl")
model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)

# model = joblib.load("../model/model_bug_classifier.pkl")
# vectorizer = joblib.load("../model/vectorizer_bug_classifier.pkl")


def predict_category(text: str):
    from app.text_cleaner import clean_text
    cleaned = clean_text(text)
    vector = vectorizer.transform([cleaned])
    return model.predict(vector)[0]
