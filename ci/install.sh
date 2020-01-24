#!/usr/bin/env bash

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
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
    chromium-browser \
    && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US:en
export LC_ALL=en_US.UTF-8

curl -sL https://deb.nodesource.com/setup_10.x | sudo bash - && sudo apt-get install -y nodejs

curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list \
    && sudo apt-get update \
    && sudo apt-get install -y \
        yarn \
    && sudo apt-get clean && sudo rm -rf /var/lib/apt/lists/*

cd submodules/abc/cfitsio
sed -i -e 's/\r$//' configure && sh configure && make -j4
cd ..
qmake . && make -j4 && sudo make install
cd ../..

pip install --user --no-deps -r requirements.txt --src src

sudo yarn global add yuglify

sudo gem install compass

./scripts/compilemessages.sh
