FROM haproxy:1.7
COPY docker/haproxy.conf /usr/local/etc/haproxy/haproxy.cfg
