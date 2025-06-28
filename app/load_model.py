import joblib
import os
from gensim.models import Word2Vec

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# model_path = os.path.join(os.path.dirname(
#     __file__), "..", "model", "model_bug_classifier.pkl")
# vectorizer_path = os.path.join(os.path.dirname(
#     __file__), "..", "model", "vectorizer_bug_classifier.pkl")
# model = joblib.load(model_path)
# vectorizer = joblib.load(vectorizer_path)

# # model = joblib.load("../model/model_bug_classifier.pkl")
# # vectorizer = joblib.load("../model/vectorizer_bug_classifier.pkl")


# def predict_category(text: str):
#     from app.text_cleaner import clean_text
#     cleaned = clean_text(text)
#     vector = vectorizer.transform([cleaned])
#     return model.predict(vector)[0]

model_path = os.path.join(os.path.dirname(
    __file__), "..", "model", "model_word2vec_classifier.pkl")
w2v_path = os.path.join(os.path.dirname(
    __file__), "..", "model", "word2vec_gensim.model")

model = joblib.load(model_path)
w2v_model = Word2Vec.load(w2v_path)


def get_w2v_vector(tokens, model, vector_size):
    vectors = [model.wv[word] for word in tokens if word in model.wv]
    if len(vectors) == 0:
        import numpy as np
        return np.zeros(vector_size)
    else:
        import numpy as np
        return np.mean(vectors, axis=0)


def predict_category(text: str):
    from app.text_cleaner import clean_text
    cleaned = clean_text(text)
    tokens = cleaned.split()
    vector = get_w2v_vector(
        tokens, w2v_model, w2v_model.vector_size).reshape(1, -1)
    return model.predict(vector)[0]


model_path = "model/bert-intent-tiny-model"
admin_tokenizer = AutoTokenizer.from_pretrained(model_path)
admin_model = AutoModelForSequenceClassification.from_pretrained(model_path)
label_encoder = os.path.join(os.path.dirname(
    __file__), "..", "model", "label_encoder.pkl")


def predict_admin_intent(text: str):
    # Predict intent and extract parameters (number, category, id, keyword)
    inputs = admin_tokenizer(text, return_tensors="pt",
                             truncation=True, padding=True, max_length=64)
    with torch.no_grad():
        outputs = admin_model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        prediction = torch.argmax(probs, dim=1).item()
        # Load label encoder if needed
        import joblib
        label_encoder_path = os.path.join(os.path.dirname(
            __file__), "..", "model", "label_encoder.pkl")
        label_encoder = joblib.load(label_encoder_path)
        intent = label_encoder.inverse_transform([prediction])[0]

    params = {}

    # Extract number (for latest reviews)
    import re
    match = re.search(r"\b(\d+)\b", text)
    if match:
        params["n"] = int(match.group(1))

    # Extract category (for category-based queries)
    categories = [
        "Premium Features", "User Feedbacks & Recommendations",
        "General Topics", "Ads", "Crashes and Bugs",
        "Updates", "Customer Support"
    ]
    text_lower = text.lower()
    for cat in categories:
        if cat.lower() in text_lower:
            params["category"] = cat
            break
        for word in cat.lower().split():
            if word in text_lower:
                params["category"] = cat
                break

    # Extract id for get_review_by_id
    match_id = re.search(r"id\s*(\d+)", text_lower)
    if match_id:
        params["id"] = int(match_id.group(1))

    # Extract keyword for search_by_keyword
    match_kw = re.search(r"keyword\s*[:=]?\s*([a-zA-Z0-9]+)", text_lower)
    if match_kw:
        params["keyword"] = match_kw.group(1)

    return intent, params
