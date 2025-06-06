FROM python:3.10

WORKDIR /app
ENV PYTHONPATH=/app

COPY . /app
RUN mv /app/prj_certs/* /usr/local/share/ca-certificates/

RUN update-ca-certificates

RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
