# -*- coding:utf-8 -*-
from decimal import Decimal
import os

import django
django.setup()

from common.functions import send_email

import psycopg2

import time
import datetime

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

import settings

from payment.service.Bitcoin import BitcoinRPC

from payment.models import Payment
from common.globals import WAITING, PAID, NOT_ENOUGH_MONEY_ARRIVED, NO_MONEY_ARRIVED
from django.db.models import Q
from django.db import connections

bitcoin_db_key = 'sellout_last_checked_block'

confirmations = 0

def get_last_checked_block():
    cursor = connections['bitcoin'].cursor()

    try:
        cursor.execute("SELECT value FROM bitcoin WHERE key = %s", (bitcoin_db_key,))
    except Exception as e:
        print e

    rows = cursor.fetchall()

    if len(rows) == 1:
        return rows[0][0]

    cursor.close()

    return ""

def update_last_checked_block(block):
    cursor = connections['bitcoin'].cursor()

    try:
        cursor.execute("SELECT value FROM bitcoin WHERE key = %s", (bitcoin_db_key,))
    except Exception as e:
        return False

    rows = cursor.fetchall()

    try:
        if len(rows) == 1:
            cursor.execute("UPDATE bitcoin SET value = %s WHERE key = %s", (block, bitcoin_db_key))
        else:
            cursor.execute("INSERT INTO bitcoin(key, value) VALUES (%s, %s)", (bitcoin_db_key, block, ))
    except Exception as e:
        print e
        return False

    cursor.close()

    return True

# main program
while True:
    last_checked_block = get_last_checked_block()

    try:
        bitcoin_client_rpc = BitcoinRPC(settings.PAYMENT['bitcoin']['host'], settings.PAYMENT['bitcoin']['port'],
                                 settings.PAYMENT['bitcoin']['rpcuser'], settings.PAYMENT['bitcoin']['rpcpassword'])
        transactions = bitcoin_client_rpc.list_since_block(last_checked_block)

        for transaction in transactions['transactions']:
            # POS Bills, POS Bills, POS Bills
            # POS Bills, POS Bills, POS Bills
            # POS Bills, POS Bills, POS Bills
            try:
                payment  = Payment.objects.get(Q(status=WAITING) | Q(status=NOT_ENOUGH_MONEY_ARRIVED), transaction_reference=transaction['address'], type="bitcoin")

                # transaction_reference is bitcoin reference in this case
                total_received_by_address = bitcoin_client_rpc.get_received_by_address(bill.transaction_reference, confirmations)
                total_received_by_address = Decimal(total_received_by_address)

                # we try to get timestamp of payment
                transaction_datetime = None

                if total_received_by_address > payment.amount_paid:
                    payment.amount_paid = total_received_by_address
                    payment.save()

                if total_received_by_address >= payment.total_btc:
                    if "time" in transaction:
                        payment.transaction_datetime = datetime.datetime.fromtimestamp(int(transaction["time"]))

                    payment.status = PAID
                    payment.save()

                    if settings.DEBUG:
                        print "Just got payment for "
                        print Payment

                    # we have this here so I will remember when doing subscriptions
                    # Subscription.extend_subscriptions(payment)
                    # payment.send_payment_confirmation_email()

                if payment.status == WAITING:
                    datetime_created_with_offset = payment.datetime_created + datetime.timedelta(hours=int(settings.PAYMENT_OFFICER["bitcoin_payment_waiting_interval"]))

                    if datetime_created_with_offset < datetime.datetime.now():
                        if payment.amount_paid > 0:
                            payment.status = NOT_ENOUGH_MONEY_ARRIVED
                        else:
                            payment.status = NO_MONEY_ARRIVED

                        payment.save()
            except Payment.DoesNotExist:
                pass
            # POS Bills, POS Bills, POS Bills
            # POS Bills, POS Bills, POS Bills
            # POS Bills, POS Bills, POS Bills

        if transactions and last_checked_block != transactions['lastblock']:
            update_last_checked_block(transactions['lastblock'])

    except Exception, error:
        subject = "ERROR when getting transactions from bitcoin client or something..."
        message = "see subject"
        if (settings.DEBUG):
            print subject
            print message
        else:
            send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, "ERROR when getting total received by addresss",
                       message, message)

        continue

    print "Sleeping %s seconds..." % (settings.PAYMENT_OFFICER["bitcoin_check_interval"])
    time.sleep(settings.PAYMENT_OFFICER["bitcoin_check_interval"])
