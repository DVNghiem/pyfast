FROM python:3.10-alpine

RUN apk update && apk add --no-cache  tzdata git make  build-base

RUN apk add gcc
RUN apk add libffi-dev

RUN pip install gunicorn

COPY requirements.txt /
RUN pip --no-cache-dir install --upgrade pip setuptools
RUN pip --no-cache-dir install -r requirements.txt
RUN mkdir -p /webapps

COPY conf/supervisor/worker.conf /etc/supervisord.conf
COPY . /webapps
WORKDIR /webapps

RUN python3 -c "import nltk; nltk.download('punkt')"
RUN python3 -c "import nltk; nltk.download('averaged_perceptron_tagger')"
