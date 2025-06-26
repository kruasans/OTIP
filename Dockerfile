FROM python:3.10-slim

COPY ./requirements.txt /requirements.txt
ARG PROXY
RUN if [-z "$PROXY"] ; then \
	pip install --no-cache-dir --upgrade -r /requirements.txt ;\
else \
	pip install --no-cache-dir --proxy "$PROXY" --upgrade -r /requirements.txt; \
fi

# Загрузка русской модели spaCy
RUN python3 -m spacy download ru_core_news_sm

COPY ./application /application
# RUN chmod +x /application/script/wait-for-it.sh
