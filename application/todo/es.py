import elasticsearch
from starlette.responses import Response
from datetime import date, datetime, timedelta
from loguru import logger
from fastapi import HTTPException
from typing import Annotated, List, Dict, Any, Optional

logger = logger.opt(colors=True)

es = elasticsearch.Elasticsearch(["http://elasticsearch:9200"])
index_name = "todos"

pipeline_body = {
    "description": "Replace secret phrases before indexing",
    "processors": [
        {
            "gsub": {
                "field": "_source.text",
                "pattern": "(?i)совершенно секретно",
                "replacement": "не интересссно"
            }
        },
        {
            "gsub": {
                "field": "_source.text",
                "pattern": "(?i)секретно",
                "replacement": "не интерессно"
            }
        },
        {
            "gsub": {
                "field": "_source.text",
                "pattern": "(?i)для служебного пользования",
                "replacement": "не интересно"
            }
        },
        {
            "gsub": {
                "field": "_source.name",
                "pattern": "(?i)совершенно секретно",
                "replacement": "не интересссно"
            }
        },
        {
            "gsub": {
                "field": "_source.name",
                "pattern": "(?i)секретно",
                "replacement": "не интерессно"
            }
        },
        {
            "gsub": {
                "field": "_source.name",
                "pattern": "(?i)для служебного пользования",
                "replacement": "не интересно"
            }
        }
    ]
}

es.ingest.put_pipeline(id="secrecy_replacer", body=pipeline_body)

group_names = ["константин", "максим", "артем"]

index_body = {
    "settings": {
        "index": {
            "max_ngram_diff": 7
        },
        "analysis": {
            "filter": {
                "russian_stop": {
                    "type": "stop",
                    "stopwords": "_russian_"
                },
                "custom_name_stop": {
                    "type": "stop",
                    "stopwords": group_names
                },
                "snowball_russian": {
                    "type": "snowball",
                    "language": "Russian"
                }
            },
            "analyzer": {
                "substring_analyzer": {
                    "type": "custom",
                    "tokenizer": "ngram_tokenizer",
                    "filter": ["lowercase"]
                },
                "russian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "russian_stop",
                        "custom_name_stop",
                        "snowball_russian"
                    ]
                },
                "word_analyzer": {  # Новый анализатор для статистики
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "russian_stop",  # Игнорируем предлоги
                        "length"  # Отсеиваем короткие слова
                    ]
                }
            },
            "tokenizer": {
                "ngram_tokenizer": {
                    "type": "ngram",
                    "min_gram": 3,
                    "max_gram": 10,
                    "token_chars": ["letter", "digit"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "combined": {
                "type": "text",
                "analyzer": "word_analyzer",
                "fielddata": True,
                "fields": {
                    "russian": {
                        "type": "text",
                        "analyzer": "russian_analyzer"
                    }
                }
            },
            "name": {
                "type": "text",
                "analyzer": "substring_analyzer",
                "copy_to": "combined",
                "fields": {
                    "russian": {
                        "type": "text",
                        "analyzer": "russian_analyzer"
                    }
                }
            },
            "text": {
                "type": "text",
                "analyzer": "substring_analyzer",
                "copy_to": "combined",
                "fields": {
                    "russian": {
                        "type": "text",
                        "analyzer": "russian_analyzer"
                    }
                }
            },
            "text_from_file": {
                "type": "text",
                "analyzer": "substring_analyzer",
                "copy_to": "combined",
                "fields": {
                    "russian": {
                        "type": "text",
                        "analyzer": "russian_analyzer"
                    }
                }
            },
            "tag": {
                "type": "keyword"
            },
            "date_creation": {
                "type": "date"
            }
        }
    }
}

mapping = {
    "mappings": {
        "properties": {
            "name": {"type": "text"},
            "text": {"type": "text"},
            "tag": {"type": "keyword"},
            "date_creation": {"type": "date"},
        }
    }
}

activity_mapping = {
    "mappings": {
        "properties": {
            "fullname": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword"
                    }
                }
            },
            "date_creation": {
                "type": "date",
                "format": "yyyy-MM-dd"
            }
        }
    }
}

if not es.indices.exists(index="activity"):
    es.indices.create(index="activity", body=activity_mapping)

if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=index_body)
    settings = {
        "index.default_pipeline": "secrecy_replacer"
    }

    es.indices.put_settings(index="todos", body=settings)

def indexating_todo(id: int, text: str, name: str, tag: str, date_creation: date) -> Response:
    """Индексирование заметки в ElasticSerach

    :param id: Номер (id) заметки в базе данных
    :type id: int
    :param text: Поле для дполнительной информации заметки
    :type text: str
    :param name: Название заметки
    :type name: str
    :param tag: Тег заметки
    :type tag: str
    :param date_creation: Дата создания заметки в формате YYYY-MM-DD
    :type date_creation: date
    :return: Ответ от ElasticSearch
    :rtype: Response
    """
    document = {
        "name": name,
        "text": text,
        "text_from_file": "",
        "tag": tag,
        "creation_date": date_creation
    }
    response = es.index(
        index=index_name,
        id=str(id),
        body=document
    )
    return response

def indexating_todo_activity(id: int, fullname: str, date_creation: date) -> Response:
    """Индексирование информации об активности протзователей в ElasticSerach

    :param id: Номер (id) заметки в базе данных
    :type id: int
    :param fullname: Имя пользователя
    :type fullname: str
    :param date_creation: Дата создания заметки в формате YYYY-MM-DD
    :type date_creation: date
    :return: Ответ от Elastic Search 
    :rtype: Response
    """
    document = {
        "fullname": fullname,
        "creation_date": date_creation
    }
    response = es.index(
        index="activity",
        id=str(id),
        body=document
    )
    return response

def editing_todo(id: int, name: str, text: str) -> Response:
    """Изменение заметки в ElasticSerach

    :param id: Номер (id) заметки в базе данных
    :type id: int
    :param name: Название заметки
    :type name: str
    :param text: Поле для дполнительной информации заметки
    :type text: str
    :return: Ответ от ElasticSearch  
    :rtype: Response
    """
    updated_data = {
        "doc": {
            "name": name,
            "text": text
        }
    }
    response = es.update(index=index_name, id=str(id), body=updated_data)
    return response

def editing_text_from_file_todo(id: int, text_from_file: str) -> Response:
    """Изменение текста из файла, присоединяемого к заметке, в ElasticSerach

    :param id: Номер (id) заметки в базе данных
    :type id: int
    :param text_from_file: Текста из файла
    :type text_from_file: str
    :return: Ответ от ElasticSearch
    :rtype: Response
    """
    updated_data = {
        "doc": {
            "text_from_file": text_from_file
        }
    }
    response = es.update(index=index_name, id=str(id), body=updated_data)
    return response

def deleting_todo(id: int) -> Response:
    """Удаление заметки в ElasticSerach

    :param id: Номер (id) заметки в базе данных
    :type id: int
    :return: Ответ от ElasticSearch
    :rtype: Response
    """
    if not es.exists(index=index_name, id=str(id)):
        return False, f"Документ с ID {id} не существует"
    return es.delete(index=index_name, id=str(id))

def find_ids_by_tag(tag: str) -> list:
    """Поиск по тегам в ElasticSearsh

    :param tag: Тег заметки, по которому будет произведён поиск
    :type tag: str
    :return: Список номеров (id) заметок в базе данных
    :rtype: list
    """
    query = {
        "query": {
            "match": {
                "tag": str(tag)
            }
        }
    }
    response = es.search(index=index_name, body=query)
    ids_list = []
    for hit in response['hits']['hits']:
        ids_list.append(hit['_id'])
    return ids_list

def find_by_date(date: str) -> list:
    """Поиск по дате в ElasticSearsh

    :param date: Дата для поиска
    :type date: str
    :return: Список номеров (id) заметок в базе данных
    :rtype: list
    """
    ids_list = []
    try:
        dt_object = datetime.strptime(date, "%Y-%m-%d").date()
        query = {
            "query": {
                "range": {
                    "creation_date": {
                        "gte": dt_object
                    }
                }
            }
        }
        response = es.search(index=index_name, body=query)
        for hit in response['hits']['hits']:
            ids_list.append(hit['_id'])
        return ids_list
    except ValueError:
        return []

def find_by_text(text: str) -> list:
    """Поиск по полю text в ElasticSearsh

    :return: Текст для поиска
    :rtype: Список номеров (id) заметок в базе данных
    """
    ids_list = []
    query = {
        "query": {
            "multi_match": {
                "query": text,
                "fields": ["name", "text", "text_from_file"]
            }
        }
    }
    response = es.search(index=index_name, body=query)
    for hit in response['hits']['hits']:
        ids_list.append(hit['_id'])
    return ids_list

async def get_user_activity(username:str) -> dict:
    """Получение активность пользователя из ElasticSearch

    :param username: Имя пользователя
    :type username: str
    :raises HTTPException: Если ElasticSearch недоступен, то получаем исключение (500)
    :return: Словарь {Дни: list, Количество заметок: list, Имя пользователя: str}
    :rtype: dict
    """
    start_date = date.today().replace(month=1, day=1).strftime('%Y-%m-%d')
    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"fullname.keyword": username}},
                    {"range": {
                        "creation_date": {
                            "gte": start_date,
                            "lte": "now/d"
                        }
                    }}
                ]
            }
        },
        "aggs": {
            "activity_by_day": {
                "date_histogram": {
                    "field": "creation_date",
                    "calendar_interval": "day",
                    "format": "yyyy-MM-dd"
                }
            }
        },
        "size": 0
    }
    result = []
    try:
        result = es.search(index="activity", body=query)
    except elasticsearch.TransportError as e:
        logger.error(f"Elasticsearch error: {e}")
        raise HTTPException(status_code=500)
    
    days = []
    counts = []

    for bucket in result["aggregations"]["activity_by_day"]["buckets"]:
        days.append(bucket["key_as_string"][:10])
        counts.append(bucket["doc_count"])
    print(days, counts)
    return {"days": days, "counts": counts, "username": username}
    
async def get_unique_users() -> list:

    """Получение списка уникальных пользователей

    :raises HTTPException: Если ElasticSearch недоступен, то получаем исключение (500)
    :return: Список уникальных пользвателей
    :rtype: list
    """
    try:
        result = es.search(index="activity", body={
            "size": 0,
            "aggs": {
                "unique_users": {
                    "terms": {
                        "field": "fullname.keyword",
                        "size": 1000
                    }
                }
            }
        })
    except elasticsearch.TransportError as e:
        logger.error(f"Elasticsearch error: {e}")
        raise HTTPException(status_code=500)
    return [bucket["key"] for bucket in result["aggregations"]["unique_users"]["buckets"]]

def get_aggregation_data(interval: str) -> List[Dict[str, Any]]:
    """Агрегирование данных по дате

    :param interval: Календарный интервал (день, неделя, месяц)
    :type interval: str
    :return: Список словарей формата {interval: интервал, doc_count: количество документов, interval_type: тип интервала}
    :raises HTTPException: ElasticSearch недоступен, то получаем исключение (500)
    :rtype: List[Dict[str, Any]]
    """
    query = {
        "size": 0,
        "aggs": {
            "by_interval": {
                "date_histogram": {
                    "field": "creation_date",
                    "calendar_interval": interval,
                    "format": "yyyy-MM-dd",
                    "min_doc_count": 1
                }
            }
        }
    }
    
    try:
        result = es.search(index="todos", body=query)
        buckets = result["aggregations"]["by_interval"]["buckets"]
        return [
            {
                "interval": bucket["key_as_string"],
                "doc_count": bucket["doc_count"],
                "interval_type": interval
            }
            for bucket in buckets
        ]
    except elasticsearch.TransportError as e:
        logger(f"Error getting aggregation data: {str(e)}")
        raise HTTPException(status_code=500)

def get_todos_for_interval(interval: str, date: str) -> List[str]:

    """Получае ID задач для конкретного интервала

    :param interval: Тип временного интервала
    :type interval: str
    :param date: Дата
    :type date: str
    :return: Список номеров (id) заметок
    :raises HTTPException: Если ElasticSearch недоступен, то получаем исключение (500)
    :rtype: List[str]
    """
    try:
        # Для дней - точное совпадение даты
        if interval == "1d":
            query = {
                "query": {
                    "term": {
                        "creation_date": date
                    }
                },
                "size": 1000,
                "_source": False
            }
        # Для недель и месяцев - диапазон дат
        else:
            start_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            if interval == "1w":
                end_date = start_date + datetime.timedelta(days=7)
            else:  # месяц
                if start_date.month == 12:
                    end_date = datetime.datetime(start_date.year + 1, 1, 1)
                else:
                    end_date = datetime.datetime(start_date.year, start_date.month + 1, 1)
            
            query = {
                "query": {
                    "range": {
                        "creation_date": {
                            "gte": start_date.strftime("%Y-%m-%d"),
                            "lt": end_date.strftime("%Y-%m-%d")
                        }
                    }
                },
                "size": 1000,
                "_source": False
            }
        
        result = es.search(index="todos", body=query)
        return [hit["_id"] for hit in result["hits"]["hits"]]
    except elasticsearch.TransportError as e:
        logger(f"Error getting todos: {str(e)}")
        raise HTTPException(status_code=500)
    
def get_top_10() -> List[Dict[str, int]]:
    search_body = {
            "size": 0,
            "aggs": {
                "top_words": {
                    "terms": {
                        "field": "combined",
                        "size": 10,
                        "order": {"_count": "desc"}
                    }
                }
            }
        }
    terms = list()
    try:
        res = es.search(index=index_name, body=search_body)
        terms = res["aggregations"]["top_words"]["buckets"]
    except elasticsearch.TransportError as e:
        logger(f"Error getting aggregation data: {str(e)}")
        raise HTTPException(status_code=500)
    return terms