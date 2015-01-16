#!/usr/local/bin/bash -e

export DJANGO_SETTINGS_MODULE=settings
export PYTHONPATH=$PYTHONPATH:/usr/local/www/
cd /usr/local/www/sellout_biz
python bin/sellout_bitcoin_payment_officer.py
