# -*- coding:utf-8 -*-
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import requests
from common.globals import PAID
from pos.models import Bill
import settings


class AfterResponse(HttpResponse):
    """
    kudos: http://stackoverflow.com/questions/4313508/execute-code-in-django-after-response-has-been-sent-to-the-client
    """
    request = None

    def close(self):
        super(AfterResponse, self).close()

        if self.status_code == 200:
            # now we do da shit
            data = self.request.POST.copy()
            data['cmd'] = "_notify-validate"
            url = ""

            if settings.DEBUG:
                url = settings.PAYMENT['paypal']['sandbox_ipn_endpoint']
            else:
                url = settings.PAYMENT['paypal']['live_ipn_endpoint']

            response = requests.post(url, data=data)

            if response and response.status_code == requests.codes.ok:
                if response.text == "VERIFIED":
                    invoice_number = self.request.POST.get('invoice_number', '')
                    invoice_id = self.request.POST.get('invoice_id', '')
                    payment_status = self.request.POST.get('payment_status', '')

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