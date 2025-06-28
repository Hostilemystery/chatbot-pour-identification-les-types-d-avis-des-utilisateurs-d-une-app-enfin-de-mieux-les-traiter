# bert_intent_training_fast.py

import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, f1_score
import re

# 1. Load dataset
df = pd.read_csv("data/Admin_NLP_Training_Data.csv")

# 2. Encode labels
label_encoder = LabelEncoder()
df['label'] = label_encoder.fit_transform(df['intent'])
joblib.dump(label_encoder, "model/label_encoder.pkl")

# 3. Tokenizer and model (small + fast)
model_name = "prajjwal1/bert-tiny"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=len(label_encoder.classes_))

# 4. Text cleaning


def clean_text(text):
    text = re.sub(r"\s+", " ", text)  # Remove extra whitespace
    text = text.strip()
    return text


# 5. Tokenization


def preprocess(example):
    cleaned = clean_text(example['text'])
    return tokenizer(cleaned, truncation=True, padding='max_length', max_length=32)


# 6. Prepare HuggingFace Dataset
dataset = Dataset.from_pandas(df[['text', 'label']])
dataset = dataset.train_test_split(test_size=0.2)
encoded_dataset = dataset.map(preprocess, batched=True)
encoded_dataset.set_format(type='torch', columns=[
                           'input_ids', 'attention_mask', 'label'])

# 7. Training Arguments
training_args = TrainingArguments(
    output_dir="bert-intent-tiny",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=1,
    weight_decay=0.01,
    logging_dir="logs",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy"
)

# 8. Evaluation metrics


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    preds = predictions.argmax(-1)
    return {
        'accuracy': accuracy_score(labels, preds),
        'f1': f1_score(labels, preds, average='weighted')
    }


# 9. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=encoded_dataset['train'],
    eval_dataset=encoded_dataset['test'],
    tokenizer=tokenizer,
    compute_metrics=compute_metrics
)

# 10. Train
trainer.train()

# 11. Save model and tokenizer
model.save_pretrained("model/bert-intent-tiny-model")
tokenizer.save_pretrained("model/bert-intent-tiny-model")
