#!/usr/bin/env bash

mkdir -p /dockerdata/log/payserver
mkdir -p /dockerdata/log/supervisor

python /opt/www/PAYUNION_SERVER/payserver/manage.py migrate --noinput

supervisord -n
