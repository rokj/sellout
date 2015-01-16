#!/usr/local/bin/bash

# Replace these three settings.
export DJANGO_SETTINGS_MODULE=settings
PROJDIR="/usr/local/www/sellout_biz"
PIDFILE="$PROJDIR/pos.pid"

cd $PROJDIR

git pull

if [ -f $PIDFILE ]; then
    # kill -9 `ps -aux | grep uwsgi | awk '{print $2}'
    echo "Stopping server..."
    uwsgi --stop $PIDFILE
    sleep 3
fi

# echo "Removing .pyc files..."
# rm `find . -name "*.pyc"`

echo "Starting server..."
cd $PROJDIR
uwsgi --wsgi-file /usr/local/www/sellout_biz/wsgi.py --python-path /usr/local/www/ --fastcgi-socket --ini pos.ini
