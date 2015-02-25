#!/usr/local/bin/bash

######         
###### spletna-blagajna.si
######            

# Replace these three settings.
export DJANGO_SETTINGS_MODULE=spletna_blagajna_settings
PROJDIR="/usr/local/www/sellout_biz"
PIDFILE="$PROJDIR/spletna-blagajna.pid"

cd $PROJDIR

git pull

if [ -f $PIDFILE ]; then
    # kill -9 `ps -aux | grep uwsgi | awk '{print $2}'
    echo "Stopping server for spletna-blagajna.si"
    uwsgi --stop $PIDFILE
    sleep 3
fi

echo "Starting server for spletna-blagajna.si."
cd $PROJDIR
uwsgi --wsgi-file /usr/local/www/sellout_biz/spletna_blagajna_wsgi.py --python-path /usr/local/www/ --fastcgi-socket --ini spletna-blagajna.ini
