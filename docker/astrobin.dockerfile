# Get the base
FROM ubuntu:16.04
MAINTAINER Salvatore Iovene <salvatore@astrobin.com>

# Install build prerequisites
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    pkg-config \
    libxslt1-dev \
    libxml2-dev \
    cmake \
    qt4-qmake \
    libqt4-dev \
    gettext \
    python-pip \
    python-pyside libpyside-dev \
    libqjson-dev libraw-dev \
    shiboken libshiboken-dev \
    libjpeg62 libjpeg62-dev \
    libfreetype6 libfreetype6-dev \
    zlib1g-dev \
    && apt-get clean && rm -rf /etc/lib/apt/lists/*

# System hacks
RUN ln -s /usr/lib/x86_64-linux-gnu/libraw.so /usr/lib/x86_64-linux-gnu/libraw.so.10

# Install abc
RUN mkdir -p /code/abc
WORKDIR /code
COPY submodules/abc /code/abc
RUN cd /code/abc/cfitsio &&  \
    ./configure && make -j4 && \
    cd /code/abc && \
    qmake . && \
    make -j4 && make install

# Install pip dependencies
COPY requirements.txt /code
RUN pip install -U setuptools && \
    pip install -U pip && \
    pip install --no-deps -r requirements.txt --src /src

CMD gunicorn wsgi:application -w 2 -b :8083
EXPOSE 8083
COPY . /code
