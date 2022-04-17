FROM debian:9.13-slim
LABEL maintainer "Alexey Petrunev alexey_petrunev@epam.com"

RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	python3 \
	python3-venv \
	python3-pip \
	python3-dev \
	build-essential \
	libssl-dev \
	libffi-dev \
	python3-setuptools && \
	rm -rf /var/lib/apt/lists/*

COPY front.py wsgi.py /opt/app/
WORKDIR /opt/app
RUN pip3 install wheel && \
    pip3 install uwsgi flask
ENTRYPOINT [ "uwsgi", "--socket", "0.0.0.0:5000" , "--protocol=http", "-w", "wsgi:app" ]
EXPOSE 5000
