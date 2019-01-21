# Get the base
FROM ubuntu:16.04
MAINTAINER Salvatore Iovene <salvatore@astrobin.com>

# Install build prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    rsyslog \
    logrotate \
    apt-transport-https \
    curl \
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
    ruby ruby-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs

# Install yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y \
        yarn \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# System hacks
RUN ln -s /usr/lib/x86_64-linux-gnu/libraw.so /usr/lib/x86_64-linux-gnu/libraw.so.10

# Install abc
COPY submodules/abc /code/submodules/abc
WORKDIR /code/submodules/abc/cfitsio
RUN sed -i -e 's/\r$//' configure && sh configure && make -j4
WORKDIR /code/submodules/abc
RUN qmake . && make -j4 && make install

# Install pip dependencies
COPY requirements.txt /code
WORKDIR /code
RUN python -m pip install --upgrade setuptools && \
    python -m pip install --upgrade pip && \
    pip install --no-deps -r requirements.txt --src /src

# Install global node dependencies
RUN yarn global add \
    yuglify

# Install compass
RUN gem install compass

# Install logrotate file
COPY docker/astrobin.logrotate.conf /etc/logrotate.d/astrobin
RUN chown root:root /etc/logrotate.d/astrobin && chmod 644 /etc/logrotate.d/astrobin

CMD python manage.py migrate --noinput && gunicorn wsgi:application -w 2 -b :8083
EXPOSE 8083
COPY . /code

RUN scripts/compilemessages.sh
