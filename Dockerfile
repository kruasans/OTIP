FROM python:3.10-slim

COPY ./requirements.txt /code/requirements.txt
ARG PROXY
RUN if [-z "$PROXY"] ; then \
	pip install --no-cache-dir --upgrade -r /code/requirements.txt ;\
else \
	pip install --no-cache-dir --proxy "$PROXY" --upgrade -r /code/requirements.txt; \
fi

COPY ./app /code/app
WORKDIR /code/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0","--reload", "--port", "80"]



