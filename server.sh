#!/bin/sh
# `/sbin/setuser www-data` runs the given command as the user `www-data`.
if [ -d "/opt/thief" ]; then
    WORKING="/opt/thief"
else
    WORKING="."
fi

cd $WORKING

python3 -m venv venv && \
. venv/bin/activate && \
pip3 install -U pip && \
pip3 install wheel && \
pip3 install --upgrade  -r requirements.txt

if [ ! -d "$WORKING/log/" ];then
    exec $WORKING/venv/bin/python $WORKING/server.py
else
    exec $WORKING/venv/bin/python $WORKING/server.py >> $WORKING/log/$(date "+%Y%m%d-%H%M%S").log 2>&1
fi

