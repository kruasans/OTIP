import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Загружаем русскую модель spaCy
nlp = spacy.load("ru_core_news_sm")

async def preprocess_sentences(text: str) -> list:
    """Разделение текста на предложения. Слова с количеством слов < 10 не рассматриваются 

    :param text: Исходный текст
    :type text: str
    :return: Список предложений
    :rtype: list
    """
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
    return sentences

async def summarize(text: str, 
                    num_sentences: int = 3) -> str:
    """Получение реферированного текста из исходного

    :param text: Текст, который будет подлежать реферированию
    :type text: str
    :param num_sentences: Количество предложений на выходе, defaults to 3
    :type num_sentences: int, optional
    :return: Реферированный текст
    :rtype: str
    """
    if text is None:
        return ""
    sentences = await preprocess_sentences(text)
    if len(sentences) <= num_sentences:
        return text  # если мало предложений — возвращаем как есть

    # TF-IDF по предложениям
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)

    # Вычисляем среднюю "важность" предложений
    sentence_scores = tfidf_matrix.sum(axis=1).A1

    # Получаем индексы самых значимых предложений
    top_indices = sentence_scores.argsort()[-num_sentences:][::-1]

    # Возвращаем предложения в исходном порядке
    top_indices_sorted = sorted(top_indices)
    summary = [sentences[i] for i in top_indices_sorted]
    print(summary)
    return " ".join(summary)