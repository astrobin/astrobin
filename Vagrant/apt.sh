#!/bin/sh

# Init
apt-get update
apt-get -y upgrade


# Install packages
apt-get -y install \
    pkg-config \
	nginx \
	memcached \
	postgresql \
	libpq-dev \
	python-pip \
	python-dev \
	git \
	libxslt1-dev \
	libxml2-dev \
	cmake \
	qt4-qmake \
	libqt4-dev \
	sudo \
    python-virtualenv \
    supervisor \
    rabbitmq-server \
    python-pyside libpyside-dev \
    libqjson-dev libraw-dev \
    shiboken libshiboken-dev

