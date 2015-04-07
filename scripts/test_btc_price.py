import os

import django
django.setup()

from common.functions import calculate_btc_price

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webpos.settings")

btc_price = calculate_btc_price("EUR", 0.5)

print btc_price