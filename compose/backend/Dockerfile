FROM debian:9.13-slim
LABEL maintainer "Alexey Petrunev alexey_petrunev@epam.com"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get -y --no-install-recommends install \
	python3 \
	python3-venv \
	python3-pip \
	python3-dev \
	build-essential \
	libssl-dev \
	libffi-dev \
        libpq-dev \
	python3-setuptools && \
	rm -rf /var/lib/apt/lists/*

COPY app.py requirements.txt /opt/app/
WORKDIR /opt/app
RUN pip3 install -r requirements.txt
ENTRYPOINT [ "./app.py" ]
