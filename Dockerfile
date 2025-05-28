FROM python:3.10

WORKDIR /app
ENV PYTHONPATH=/app

COPY . /app
RUN mv /app/http_ca.crt /usr/local/share/ca-certificates/http_ca.crt && update-ca-certificates

RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
