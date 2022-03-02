# Get the base
FROM ubuntu:20.04
MAINTAINER Salvatore Iovene <salvatore@astrobin.com>

ARG DEBIAN_FRONTEND=noninteractive
ARG APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1

RUN echo `uname -r`

RUN <<EOR
# Debian glibc won't install on kernel revisions >=255, so add a wrapper script
# to clamp the revision number. Without also patching the uname syscalls,
# glibc's version math will overflow, resulting in an increased minor version
# number and possibly in glibc trying to use unavailable syscalls or features.
if [ ! -e /bin/uname.bin -a ! -e /usr/bin/uname.bin ]; then
    for uname in /bin/uname /usr/bin/uname; do
        # We don't use --rename since /bin may be a temp symlink to /usr/bin.
        # --no-rename doesn't exist on old dpkg, but --rename will become the
        # default in the future, so we have to try both with and without.
        dpkg-divert --divert "$uname.bin" --no-rename "$uname" 2>/dev/null \
            || dpkg-divert --divert "$uname.bin" "$uname"
        mv -f "$uname" "$uname.bin" 2>/dev/null || true
    done
    echo '#!/bin/sh -eu
uname.bin "$@" | sed '\''s/\.\(25[5-9]\|2[6-9][0-9]\|[3-9][0-9][0-9]\)-/.254-/g'\' > /bin/uname
    chmod +x /bin/uname
fi
EOR

RUN echo `uname -r`

# Install build prerequisites
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    rsyslog \
    logrotate \
    apt-transport-https \
    curl \
    git \
    build-essential \
    python3-dev \
    pkg-config \
    libxslt1-dev \
    libxml2-dev \
    gettext \
    python3-pip \
    libjpeg8 libjpeg8-dev libjpeg-dev \
    libtiff5 libtiff5-dev libtiff-tools \
    libfreetype6 libfreetype6-dev \
    liblcms2-dev \
    zlib1g-dev \
    libcairo2 \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    ruby ruby-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Set the locale
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && apt-get install -y nodejs

# Install pip dependencies
RUN mkdir /code
COPY requirements.txt /code
WORKDIR /code
RUN pip3 install --upgrade pip && \
    pip3 install setuptools && \
    pip3 install --no-deps -r requirements.txt --src /src

# Install global node dependencies
RUN npm install -g yuglify

# Install compass
RUN gem install compass
COPY astrobin/static/astrobin/scss/*.scss astrobin/static/astrobin/scss/
RUN mkdir -p astrobin/static/astrobin/css
RUN sass astrobin/static/astrobin/scss/astrobin.scss astrobin/static/astrobin/css/astrobin.css

# Install logrotate file
COPY docker/astrobin.logrotate.conf /etc/logrotate.d/astrobin
RUN chown root:root /etc/logrotate.d/astrobin && chmod 644 /etc/logrotate.d/astrobin

# Set up permissions for logging in DEBUG mode
RUN touch debug.log && chmod 777 debug.log

CMD python manage.py migrate --noinput && gunicorn wsgi:application -w 2 -b :8083
EXPOSE 8083
EXPOSE 8084
COPY . /code

RUN scripts/compilemessages.sh
