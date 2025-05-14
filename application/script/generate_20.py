import requests

def main():
    # Укажите URL вашего FastAPI сервера
    url = "http://127.0.0.1:80/todo/generate_20"
    
    try:
        # Отправляем POST-запрос
        response = requests.post(url)
        
        # Проверяем статус ответа
        if response.status_code == 200:
            print("Запрос успешно выполнен!")
            print("Ответ сервера:", response.json())
        else:
            print(f"Ошибка! Статус код: {response.status_code}")
            print("Ответ сервера:", response.text)
    except Exception as e:
        print(f"Произошла ошибка при отправке запроса: {e}")

if __name__ == "__main__":
    main()