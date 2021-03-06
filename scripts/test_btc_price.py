import os

import django
from payment.service.Bitcoin import BitcoinRPC
import settings

django.setup()

from common.functions import calculate_btc_price

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

btc_price = calculate_btc_price("EUR", 0.5)

print btc_price

bitcoin_rpc = BitcoinRPC(settings.PAYMENT['bitcoin']['host'], settings.PAYMENT['bitcoin']['port'], settings.PAYMENT['bitcoin']['rpcuser'], settings.PAYMENT['bitcoin']['rpcpassword'])
address = bitcoin_rpc.get_new_address("rokj_text")


