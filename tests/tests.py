# -*- coding:utf-8 -*-

import os
import string
import urllib
import django

import settings

django.setup()

from django.http import QueryDict
from bl_auth import User
from blusers.forms import BlocklogicUserBaseForm
from blusers.models import BlocklogicUser
from pos.models import Permission, Company
from pos.views.manage.company import CompanyForm
from payment.service.Bitcoin import BitcoinRPC
from common.functions import calculate_btc_price, get_random_string

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

print bcolors.WARNING + "We do some tests, right?" + bcolors.ENDC
print bcolors.OKGREEN + bcolors.BOLD + "Grosuplje p0wah!" + bcolors.ENDC
print

### TESTS ###
### TESTS ###
### TESTS ###

# helper function
def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict

# now real tests
try:
    ### btc price ###
    if "calculate_btc_price" in settings.TESTS:
        print "---"
        print "Will try to calculate BTC price..."
        btc_price = calculate_btc_price("EUR", 0.5)
        print "BTC price for 0.5 EUR is ", btc_price
        print "---"
        print

    ### btc address ###
    if "btc_address" in settings.TESTS:
        print "---"
        print "Will try to get new BTC address..."
        bitcoin_rpc = BitcoinRPC(settings.PAYMENT['bitcoin']['host'], settings.PAYMENT['bitcoin']['port'], settings.PAYMENT['bitcoin']['rpcuser'], settings.PAYMENT['bitcoin']['rpcpassword'])
        address = bitcoin_rpc.get_new_address("rokj_text")
        print "New BTC address for rokj_text is ", address
        print "---"
        print

    if "create_user" in settings.TESTS:
        print "---"
        print "Will try create new user with email rok.jaklic@gmail.com..."

        my_dict = {
            u'email': u'rok.jaklic@gmail.com',
            u'first_name': u'Rok TEST',
            u'last_name': u'Jaklic TEST',
            u'password1': u'rok123',
            u'password2': u'rok123',
            u'country': u'SI',
            u'sex': u'male'
        }

        query_string = urllib.urlencode(my_dict)
        query_dict = QueryDict(query_string)

        user_form = BlocklogicUserBaseForm(query_dict)

        if user_form.is_valid():
            email = user_form.cleaned_data['email']

            if User.exists(email):
                print "User exists, something wrong, check it out..."
                raise Exception

            new_user = user_form.save()
            new_user.set_password(user_form.cleaned_data['password1'])

            key = ""
            while key == "":
                key = get_random_string(15, string.lowercase + string.digits)
                user = BlocklogicUser.objects.filter(password_reset_key=key)

                if user:
                    key = ""

            new_user.password_reset_key = key
            new_user.type = 'normal'
            new_user.is_active = False
            new_user.save()
        else:
            print "User form not valid"
            print user_form.errors

            BlocklogicUser.objects.get(email='rok.jaklic@gmail.com').delete()

            raise Exception

        print "New created successfully created..."
        print "---"
        print


    ### creating company ###
    if "create_company" in settings.TESTS:
        print "---"
        print "Will try create new company Neko podjetje d.o.o...."

        my_dict = {
            u'website': 'http://www.spletna-stran.com',
            u'city': u'Velike Lasce',
            u'url_name': u'neko-podjetje',
            u'name': u'Neko podjetje d.o.o.',
            u'country': u'SI',
            u'notes': u'',
            u'vat_no': u'SI20453213',
            u'phone': u'041256411',
            u'street': u'Rasica 13',
            u'tax_payer': u'False',
            u'postcode': u'1315',
            u'email': u'rok.jaklic@gmail.com'
        }

        query_string = urllib.urlencode(my_dict)
        query_dict = QueryDict(query_string)

        form = CompanyForm(query_dict)

        if form.is_valid():
            company = form.save(False)
            company.created_by = new_user
            form.save()

            # add 'admin' permissions for the user that registered this company
            default_permission = Permission(
                created_by=new_user,

                user=new_user,
                company=company,
                permission='admin',
            )
            default_permission.save()

            print "New company successfully created..."
        else:
            print "---"
            print "Company form not valid"

            Company.objects.get(url_name='neko-podjetje').delete()

            raise Exception

        print "---"
        print

    ### destroying data ###
    print "Will delete test data..."
    default_permission.delete()
    company.delete()
    new_user.delete()

except Exception as e:
    try:
        default_permission.delete()
    except:
        pass

    try:
        company.delete()
    except:
        pass

    try:
        new_user.delete()
    except:
        pass

    print e

