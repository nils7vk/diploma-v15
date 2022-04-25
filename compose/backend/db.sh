#!/bin/sh

CUR_DIR=$(pwd)

. ./env_file

docker volume create db
docker run --name potgres -d \
	-e POSTGRES_DB=$POSTGRES_DB \
	-e POSTGRES_USER=$POSTGRES_USER \
	-e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
	-v db:/var/lib/postgresql/data \
        -p 5432:5432 \
	postgres:14-alpine
