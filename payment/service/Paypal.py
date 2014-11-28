import datetime
import json
import requests
from common.models import TemporaryStorage
from payment.service.ServiceAbstract import ServiceAbstract
import settings
from django.utils.translation import ugettext as _


class Paypal(ServiceAbstract):
    token_url = {"method": "POST", "url": settings.PAYMENT["paypal"]["url"] + "/v1/oauth2/token"}
    payment_url = {"method": "POST", "url": settings.PAYMENT["paypal"]["url"] + "/v1/payments/payment"}
    response = None

    def __init__(self):
        self.client_id = settings.PAYMENT["paypal"]["client_id"]
        self.secret = settings.PAYMENT["paypal"]["secret"]

    def _try_to_get_token(self):
        token = None

        i = 0
        while not token:
            if i == 2:
                break

            token = self._get_token()
            i += 1

        return token

    def _get_token(self):
        try:
            ts = TemporaryStorage.objects.get(key="paypal_token")
            value = json.loads(ts.value)

            if "expires_in" in value:
                datetime_expires = datetime.datetime.strptime(value["expires_in"], '%Y-%m-%d %H:%M:%S')
                if datetime.datetime.now() < datetime_expires:
                    return value["access_token"]

        except TemporaryStorage.DoesNotExist:
            pass

        user = settings.PAYMENT["paypal"]["client_id"]
        password = settings.PAYMENT["paypal"]["secret"]

        headers = {"Accept": "application/json", "Accept-Language": "en_US",
                   "Content-Type": "application/x-www-form-urlencoded"}
        params = {"grant_type": "client_credentials"}
        response = self._send_request(url=self.token_url["url"], method=self.token_url["method"], params=params,
                                      data={}, headers=headers, auth={"user": user, "pass": password})

        if not response:
            if settings.DEBUG:
                print response

            return None

        response = response.json()
        if "access_token" in response and "expires_in" in response:
            datetime_expires = datetime.datetime.now() + datetime.timedelta(seconds=int(response["expires_in"]))
            value = json.dumps({"expires_in": datetime_expires.strftime("%Y-%m-%d %H:%M:%S"), "access_token": response["access_token"]})

            try:
                ts
            except NameError:
                ts = TemporaryStorage(key="paypal_token", value=value)

            ts.value = value
            ts.save()

            return response["access_token"]

        return None

    def pay(self, amount, currency, duration, return_url, cancel_url):
        """
        This method actually gets approval for payment. After that we have to execute! payment.

        @param amount:
        @param currency: curr
        @param duration:
        @param return_url:
        @param cancel_url:
        @return: True or False
        """

        token = self._try_to_get_token()

        if not token:
            return False

        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json"}
        data = {
            "intent": "sale",
            "redirect_urls":
                {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
            "payer":
                {
                    "payment_method": "paypal"
                },
            "transactions":
                [
                    {
                        "item_list": {
                            "items": [
                                {
                                    "name": _("Subscription for %s month/s for timebits.com" % (duration)),
                                    "price": str(amount),
                                    "currency": currency,
                                    "quantity": 1
                                }
                            ]
                        },
                        "amount":
                        {
                             "total": str(amount),
                             "currency": currency
                        },
                        "description": _("You selected paypal as payment. When you approve payment, you will be redirect back to the site.")
                    }
                ]
        }

        response = self._send_request(url=self.payment_url["url"], method=self.payment_url["method"], params={},
                                      data=json.dumps(data), headers=headers)

        if not response:
            return False

        self.response = response.json()

        if "state" not in self.response:
            if settings.DEBUG:
                print self.response
                pass

            return False

        if self.response["state"] != "created":
            return False

        if response.status_code == requests.codes.created:
            return True

        return False

    def execute_payment(self, approve_url, payer_id):
        token = self._try_to_get_token()

        if not token:
            return False

        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json", "Accept": "application/json"}
        data = {
            "payer_id": payer_id,
        }

        response = self._send_request(url=approve_url, method=self.payment_url["method"], params={},
                                      data=json.dumps(data), headers=headers)

        if not response:
            return False

        self.response = response.json()

        if response.status_code == requests.codes.ok:
            return True

        return False