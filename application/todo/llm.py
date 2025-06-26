import requests

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
    return response.json()["choices"][0]["message"]["content"].strip()
