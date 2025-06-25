import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from textblob import TextBlob
import string
import nltk

nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('wordnet')
nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()


def correct_spelling(text):
    return str(TextBlob(text).correct())


def clean_text(text):
    # 1. Minuscule
    text = correct_spelling(text)
    text = text.lower()
    # 3. Supprimer les URLs
    text = re.sub(r"http\S+|www\S+|https\S+", " link ", text)
    # 4. Supprimer les nombres
    text = re.sub(r"\b\d+\b", "", text)
    # 5. Supprimer la ponctuation
    text = text.translate(str.maketrans("", "", string.punctuation))
    # 6. Tokenisation + stopwords
    words = text.split()
    words = [word for word in words if word not in stop_words]
    # 7. Lemmatisation
    words = [lemmatizer.lemmatize(word) for word in words]
    return " ".join(words)
