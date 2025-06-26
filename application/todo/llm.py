import requests
import json
from typing import List, Dict
import re
 

api_key = "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"

async def generate_title(details: str) -> str:
    """Генерирует краткий заголовок для заметки с помощью LLM.

    :param details: Описание заметки
    :type details: str
    :return: Сгенерированный заголовок
    :rtype: str
    """
    prompt = f"Сгенерируй один короткий заголовок по описанию и тексту:\n\nОписание:\n{details}\n\nЗаголовок:"
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "meta-llama/llama-4-maverick:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    print(response.json())
    return response.json()["choices"][0]["message"]["content"].strip()

async def cluster_todos_llm_only(
    texts: List[str],
    ids: List[int],
    todos: list,
    count_clusters: int
) -> Dict[str, list]:
    """
    Кластеризует тексты заметок с помощью LLM (без sklearn и spaCy).
    
    :param texts: Список текстов
    :param ids: Список соответствующих ID текстов
    :param todos: Список объектов Todo
    :param count_clusters: Желаемое число кластеров
    :return: Словарь {название кластера: список Todo}
    """
    if len(texts) != len(ids):
        raise ValueError("Длины списков texts и ids должны совпадать")
    text_str = ""
    i = 1
    for text in texts:
        text_str += f'{i}. {text}\n'
        i+=1
    # print(text_str)

    # Формируем запрос
    prompt = f"""
        Раздели следующие тексты на {count_clusters} смысловых группы. Именно {count_clusters}. Больше не нужно. Повторений быть не должно. Нужно чётко разделить на {count_clusters} смысловых групп. Без корректировок.
        Для каждой группы:
        - Дай короткое и точное название (2-3 слова)
        - Выведи так:
        **Группа 1: "Название группы"**
        ID: <id1>, <id2>, <id3>

        Вот тексты:
        {text_str}
        """.strip()

    for i, (id_, text) in enumerate(zip(ids, texts), 1):
        prompt += f"\n{i}. {text.strip()} (ID: {id_})"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/llama-4-maverick:free",
            "messages": [{"role": "user", "content": prompt}]
        }
    )

    try:
        content = response.json()["choices"][0]["message"]["content"].strip()
        print(content)
    except Exception as e:
        raise RuntimeError(f"Ошибка получения ответа от LLM: {e}\nRAW: {response.text}")

    # Парсим группы и id
    group_blocks = re.findall(r'\*\*Группа\s+\d+:\s+"(.+?)"\*\*\s*ID:\s*([0-9,\s]+)', content)

    if not group_blocks:
        raise RuntimeError(f"Не удалось распознать группы в ответе LLM:\n{content}")

    # Преобразуем в структуру
    todo_by_id = {todo.id: todo for todo in todos}
    clusters: Dict[str, List[Todo]] = {}

    for group_name, id_str in group_blocks:
        id_list = [int(x.strip()) for x in id_str.split(',') if x.strip().isdigit()]
        clusters[group_name] = [todo_by_id[i] for i in id_list if i in todo_by_id]
    
    print(clusters)
    return clusters
