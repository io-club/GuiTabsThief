#!/bin/sh
# `/sbin/setuser www-data` runs the given command as the user `www-data`.
cd /opt/thief || exit

python3 -m venv venv && \
. venv/bin/activate && \
pip3 install -U pip && \
pip3 install wheel && \
pip3 install --upgrade  -r requirements.txt

if [ ! -d "/opt/thief/log/" ];then
    exec /opt/thief/venv/bin/python /opt/thief/server.py >> /dev/null 2>&1
else
    exec /opt/thief/venv/bin/python /opt/thief/server.py >> /opt/thief/log/$(date "+%Y%m%d-%H%M%S").log 2>&1
fi

