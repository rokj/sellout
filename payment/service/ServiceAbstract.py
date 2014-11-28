from abc import ABCMeta, abstractmethod
from jsonrpc import json
import requests
from common.functions import send_email
import settings


class ServiceAbstract(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def pay(self, amount, currency, return_url, cancel_url):
        pass


    def _send_request(self, url, method, params, data, headers, auth={}):
        if method == "GET":
            if auth:
                response = requests.get(url, params=params, data=data, headers=headers, auth=(auth["user"], auth["pass"]))
            else:
                response = requests.get(url, params=params, data=data, headers=headers)
        elif method == "POST":
            if auth:
                response = requests.post(url, params=params, data=data, headers=headers, auth=(auth["user"], auth["pass"]))
            else:
                response = requests.post(url, params=params, data=data, headers=headers)

        if response.status_code == requests.codes.ok or response.status_code == requests.codes.created:
            return response

        if settings.DEBUG:
            subject = "Error when doing request to %s" % (url)
            message = "with params %s, data %s and headers %s and response %s" % (params, data, headers, response)

            print subject
            print message
            print response.text
            print params
            print headers
            print url

            # TODO: remove
            # send_email(settings.EMAIL_FROM, [settings.EMAIL_FROM], None, subject, message, message)

        return None