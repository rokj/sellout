#!/bin/bash

######
###### sellout.biz
######  

# Replace these three settings.
export DJANGO_SETTINGS_MODULE=settings
PROJDIR="/usr/local/www/sellout_biz"
PIDFILE="$PROJDIR/pos.pid"

cd $PROJDIR

git -c http.sslVerify=false pull

if [ -f $PIDFILE ]; then
    # kill -9 `ps -aux | grep uwsgi | awk '{print $2}'
    echo "Stopping server for sellout.biz."
    /usr/local/bin/uwsgi --stop $PIDFILE
    sleep 3
fi

# echo "Removing .pyc files..."
# rm `find . -name "*.pyc"`

echo "Starting server for sellout.biz."
cd $PROJDIR
/usr/local/bin/uwsgi --wsgi-file /usr/local/www/sellout_biz/wsgi.py --python-path /usr/local/www/ --fastcgi-socket --ini pos.ini

echo "TESTS"
echo "TESTS"
echo "TESTS"

python tests/tests.py