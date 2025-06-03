FROM python:3.10

WORKDIR /app
ENV PYTHONPATH=/app

COPY . /app
RUN mv /app/prj_certs/http_ca.crt /usr/local/share/ca-certificates/http_ca.crt
RUN mv /app/prj_certs/smtp_cert.pem /usr/local/share/ca-certificates/smtp_cert.pem
RUN mv /app/prj_certs/ca_cert_key.pem /usr/local/share/ca-certificates/ca_cert_key.pem

RUN update-ca-certificates

RUN pip3 install --upgrade setuptools
RUN pip3 install -r requirements.txt
