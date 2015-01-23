# -*- coding:utf-8 -*-
from urllib2 import urlopen
from django.http import HttpResponse, Http404, QueryDict
from django.views.decorators.csrf import csrf_exempt
import requests
from six import b
from common.globals import PAID
from pos.models import Bill
import settings
import logging


class AfterResponse(HttpResponse):
    """
    kudos: http://stackoverflow.com/questions/4313508/execute-code-in-django-after-response-has-been-sent-to-the-client
    """
    request = None
    logger = logging.getLogger(__name__)

    def query_string_to_dict(self, query_string):
        roughdecode = dict(item.split('=', 1) for item in query_string.split('&'))
        encoding = roughdecode.get('charset', None)

        if encoding is None:
            raise Http404

        query = query_string.encode('ascii')
        data = QueryDict(query, encoding=encoding).dict()

        return data

    def close(self):
        super(AfterResponse, self).close()

        if self.status_code == 200:
            # now we do da shit
            url = ""

            if settings.DEBUG:
                url = settings.PAYMENT['paypal']['sandbox_ipn_endpoint']
            else:
                url = settings.PAYMENT['paypal']['live_ipn_endpoint']

            query_string = self.request.body.decode('ascii')
            data = self.query_string_to_dict(query_string)

            response = urlopen(url, b("cmd=_notify-validate&%s" % query_string)).read()

            self.logger.debug("Let us try to validate IPN message.")

            if response:
                self.logger.debug("Just got response for IPN message.")

                if response == "VERIFIED":
                    self.logger.debug("IPN message VALID.")

                    invoice_number = data.get('invoice_number', '')
                    invoice_id = data.get('invoice_id', '')
                    payment_status = data.get('payment_status', '')

                    self.logger.debug("We will check payment for invoice number %s, with invoice id %s and payment status %s" % (invoice_number, invoice_id, payment_status))

                    if invoice_id == '' or invoice_number == '':
                        raise Http404

                    try:
                        bill = Bill.objects.get(serial=invoice_number)
                        payment = bill.payment

                        if payment.paypal_transaction_reference == invoice_id and payment_status == 'Completed':
                            if settings.DEBUG:
                                print "Just got payment with total %s and transactions reference %s" % (str(payment.total), payment.paypal_transaction_reference)

                            payment.status = PAID
                            payment.save()
                    except Bill.DoesNotExist:
                        raise Http404
                else:
                    self.logger.debug("IPN NOT VALID.")
            else:
                self.logger.debug("Could not get OK response for IPN message.")


    def set_request(self, request):
        self.request = request

# this would be the view definition
@csrf_exempt
def paypal_ipn_handler(request):
    if request.method != 'POST':
        raise Http404

    response = AfterResponse('')
    response.set_request(request)

    return response