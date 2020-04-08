#!/usr/bin/env bash

sudo apt-get update && sudo apt-get install -y --no-install-recommends \
    locales \
    rsyslog \
    logrotate \
    apt-transport-https \
    curl \
    git \
    build-essential \
    python-dev \
    pkg-config \
    libxslt1-dev \
    libxml2-dev \
    gettext \
    python-pip \
    libjpeg62 libjpeg62-dev \
    libfreetype6 libfreetype6-dev \
    liblcms2-dev \
    zlib1g-dev \
    ruby ruby-dev \
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

pip install --user --no-deps -r requirements.txt --src src

sudo yarn global add yuglify

sudo gem install compass

./scripts/compilemessages.sh
