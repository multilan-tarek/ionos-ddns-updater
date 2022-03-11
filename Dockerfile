FROM ubuntu:20.04

MAINTAINER Dockerfiles

RUN apt-get update

RUN DEBIAN_FRONTEND="noninteractive" apt-get -y install tzdata
# Install required packages and remove the apt packages cache when done.

RUN apt-get update && \
    apt-get upgrade -y && \ 	
    apt-get install -y \
  openssl \
	python3 \
	python3-dev \
	python3-setuptools \
	python3-pip && \
	pip3 install -U pip setuptools && \
   rm -rf /var/lib/apt/lists/*

RUN pip3 install dnspython


COPY ionos.py /ionos.py

CMD ["/usr/bin/python3", "-u", "/ionos.py"]