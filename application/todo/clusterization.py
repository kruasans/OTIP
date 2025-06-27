from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import spacy
import numpy as np

nlp = spacy.load("ru_core_news_sm")


def preprocess_text(texts: list) -> list:
    """Функция предобработки текста

    :param texts: Тексты
    :type texts: list
    :return: Отчищенные от стоп слов тексты
    :rtype: list
    """
    cleaned = []
    for text in texts:
        doc = nlp(text)
        lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        cleaned.append(" ".join(lemmas))
    print(cleaned)
    return cleaned



async def clusterization_texts(texts: List[str], ids: List[int], count_clusters: int) -> dict[int, List[int]]:
    """Кластеризация текстов через spaCy .vector + KMeans с очисткой от стоп-слов

    :param texts: Список текстов
    :param ids: Список номеров заметок
    :param count_clusters: Количество кластеров
    :raises ValueError: Если длины списков не совпадают
    :return: Словарь {Номер кластера: список ID заметок}
    """
    if len(texts) != len(ids):
        raise ValueError("Длина списков texts и ids должна совпадать")

    embeddings = []
    for text in texts:
        doc = nlp(text)
        # Удаляем стоп-слова и пунктуацию
        tokens = [token for token in doc if not token.is_stop and not token.is_punct]
        if tokens:
            # Усредняем векторы по токенам
            vec = np.mean([token.vector for token in tokens if token.has_vector], axis=0)
        else:
            # Если текст пустой после фильтрации — вектор из нулей
            vec = np.zeros(nlp.vocab.vectors_length)
        embeddings.append(vec)

    embeddings = np.array(embeddings)

    # Кластеризация
    kmeans = KMeans(n_clusters=count_clusters, random_state=42, n_init="auto")
    kmeans.fit(embeddings)

    labels = kmeans.labels_.tolist()

    clusters = {}
    for text_id, label in zip(ids, labels):
        clusters.setdefault(label, []).append(text_id)

    return clusters

async def group_clustered_todos(clusters: dict[int, list[int]], todos: list) -> dict[int, list]:
    """Выставляет соответствие cluster_id: todo

    :param clusters: Словарь кластеров. {Номер кластера: список заметок из этого кластера}
    :type clusters: dict[int, list[int]]
    :param todos: Список всех заметок
    :type todos: list
    :return: Словарь {id: todos}
    :rtype: dict[int, list]
    """
    todos_by_id = {todo.id: todo for todo in todos}
    grouped = {}

    for cluster_id, ids in clusters.items():
        grouped[cluster_id] = [todos_by_id[i] for i in ids if i in todos_by_id]

    return grouped
