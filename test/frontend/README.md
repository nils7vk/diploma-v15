## CMD
```sh
docker build . -t uwsgi:v1
docker run -p 5000:5000 --name uwsgi -t uwsgi:v1
```
