# fastapi-todo-lr1

## установка с прокси и без
```bash
pip install --user --proxy http://login:pass@192.168.232.1:3128 -r requirements.txt
```
```bash
pip install --user -r requirements.txt
```
```bash
cd application
```
```bash
uvicorn main:application --reload
```

Задачи на ЛР1

0. Склонировать к себе этот проект. Загрузить в личный проект по указанию преподавателя. Дополнить gitignore. Разработку вести через создание задач, веток и merge request.
1. Сделать Docker-образ, в ридми прописать режим работы пользователя (построил-запустил) и разработчика (запустил автообновляемый контейнер).
2. Подготовить postman:
    * создать коллекцию
    * через переменные окружения настроить URL
    * реализовать все запросы
    * экспортировать запросы и сохранить в своём проекте
3. Починить баги:
    * Падение при создании пустой задачи. Реализовать с помощью status\_code
    * Падение при удалении несуществующей задачи
    * Добавить ограничение на длину загружаемой записи в 500 символов
    * Есть ли ещё?
4. Доработать:
    * Отрефакторить модель, заменив task на title - заголовок задачи
    * Задачу дополнить полем details (подробное описание задачи) с произвольным текстом. На подробном представлении добавить второй textarea для details
    * На главную страницу добавить кнопку "выполнено" для невыполненных задач и "не выполнено" для выполненных. По нажатию менять статут тудушки
    * Добавить постраничный просмотр, если тудушек больше 10
    * Добавить скрипт генерации 20 тудушек со случайными заголовками. Добавить в ридми порядок запуска этого скрипта через Docker
    * Добавить в модель тег для задачи, реализовать как enum со значениями учёба/личное/планы. Добавить на страницу редактирования тудушки выпадающий список тегов


# Для работы

## Для сборки docker-образа
```bash
sudo docker build -t 2021-3-26-cha .
```

## Запуск djcker-образа для пользователя
```bash
sudo docker run --rm -p 80:80 2021-3-26-cha
```

## Запуск dpcker-образа для разработчика
```bash
sudo docker run --rm -v "${PWD}/application":/application -p 80:80 2021-3-26-cha
```

# genaration
## Build generator
```bash
sudo docker build -t 2021-3-26-cha-generate -f DockerfileGenerator .
```
## Example without argument
```bash
sudo docker run --rm --network=host 2021-3-26-cha-generate
```
## Example with argument([num] - positive integer)
```bash
sudo docker run --rm --network=host 2021-3-26-cha-generate [num]
```

# Запуск с docker-compose
## Приложение в фоне
```bash
sudo chmod +x application/script/*
mkdir -p ./elastic_data_storage
sudo chown -R 1000:1000 ./elastic_data_storage
sudo docker compose -f compose.yml up -d --build
```

## Приложение с выводом в консоль
```bash
sudo chmod +x application/script/*
mkdir -p ./elastic_data_storage
sudo chown -R 1000:1000 ./elastic_data_storage
sudo docker compose -f compose.yml up --build
```

## Тесты
```bash
sudo docker build -t 2021-3-26-cha .
sudo docker compose -f compose_tests.yml up --build
```

## Остановка
```bash
sudo docker compose down
```
