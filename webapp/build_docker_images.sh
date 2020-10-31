#!/bin/bash


# Clone and build image that has rpi support

mkdir tmp
cd tmp

git clone https://github.com/tiangolo/uwsgi-nginx-docker.git

cd uwsgi-nginx-docker/docker-images/

mv python3.8.dockerfile Dockerfile

docker build -t tiangolo/uwsgi-nginx:python3.8 .

cd ../../

# Clone and build image that is customized for Flask (uses the previous image as the base)

git clone https://github.com/tiangolo/uwsgi-nginx-flask-docker.git

cd uwsgi-nginx-flask-docker/docker-images/

mv python3.8.dockerfile Dockerfile

docker build -t tiangolo/uwsgi-nginx-flask:python3.8 .

# Run the image 
docker run -it tiangolo/uwsgi-nginx-flask:python3.8 bash
