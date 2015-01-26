import smtplib
import datetime
import requests
import psycopg2

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decimal import Decimal, ROUND_DOWN

FROM = "rokj@rasca.net"
TO = "rok@blocklogic.net"
SUBJECT = "Bitstamp price ..."

DESIRED_DIFFERENCE = 4 # in percent

def coinbase_conversion_rate():
    response = requests.get("http://finance.yahoo.com/d/quotes.csv?e=.csv&f=c4l1&s=EURUSD=X")

    result = None

    try:
        for line in response.iter_lines():
            result = line.split(",")[1]

            break
    except Exception:
        pass

    return result

def bitstamp_conversion_rate():
    response = requests.get("https://www.bitstamp.net/api/eur_usd/")

    return response.json()

def send_email(_from, to, subject, message):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = _from
    msg['To'] = to
    msg['X-Priority'] = '2'

    text = message
    html = """\
    <html>
      <head></head>
      <body>
        %s
      </body>
    </html>
    """ % (message)

    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    smtp = smtplib.SMTP('localhost')
    smtp.sendmail(_from, to, msg.as_string())

urls = {
#   "mtgox_btceur": "http://data.mtgox.com/api/2/BTCEUR/money/ticker_fast",
#   "mtgox_btcusd": "http://data.mtgox.com/api/2/BTCUSD/money/ticker_fast",
#   "bitstamp_btcusd": "https://www.bitstamp.net/api/ticker/",
    "coinbase_btcusd": "https://api.coinbase.com/v1/prices/sell"
}

price = {
    "mtgox_btceur": 0,
    "mtgox_btcusd": 0,
    "bitstamp_btcusd": 0,
    "coinbase_btcusd": 0
}

headers = {'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'application/json, text/javascript, */*; q=0.01', 'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

bitcoin_db_hostname = '127.0.0.1'
bitcoin_db_username = 'bitcoin'
bitcoin_db_password = 'bitcoin'
bitcoin_db_database = 'bitcoin'

def update_btc_price(currency, price, datetime_updated=None):
    try:
        conn=psycopg2.connect("host='%s' dbname='%s' user='%s' password='%s'" % (bitcoin_db_hostname, bitcoin_db_database, bitcoin_db_username, bitcoin_db_password, ))
    except Exception as e:
        print e
        return False

    cur = conn.cursor()

    try:
        cur.execute("SELECT value FROM bitcoin WHERE key = %s", (currency,))
    except Exception as e:
        return False

    rows = cur.fetchall()

    try:
        if len(rows) == 1:
            if datetime_updated:
                cur.execute("UPDATE bitcoin SET value = %s, datetime_updated = %s WHERE key = %s", (price, datetime_updated, currency))
            else:
                cur.execute("UPDATE bitcoin SET value = %s WHERE key = %s", (price, currency))

        else:
            cur.execute("INSERT INTO bitcoin(key, value) VALUES (%s, %s)", (currency, price, ))
    except Exception as e:
        print e
        return False

    conn.commit()
    cur.close()
    conn.close()

    return True

for exchange, url in urls.iteritems():
    response = requests.get(url, data={}, headers=headers, verify=False)

    if exchange == "bitstamp_btcusd":
        conversion_rate = bitstamp_conversion_rate()
    elif exchange == "coinbase_btcusd":
        conversion_rate = coinbase_conversion_rate()

    if response.status_code == 200:
        datetime_updated = datetime.datetime.utcnow()

        response = response.json()

        if exchange == "bitstamp_btcusd":
            if u"last" in response:
                print datetime.datetime.now()

                last_price = Decimal(response["last"])
                update_btc_price("bitstamp_1_btcusd", last_price, datetime_updated)
                print "bitstamp_1_btcusd: %s" % last_price

                price["bitstamp_1_usdbtc"] = Decimal(str(1/(last_price))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
                update_btc_price("bitstamp_1_usdbtc", price["bitstamp_1_usdbtc"], datetime_updated)
                print "bitstamp_1_usdbtc: %s" % price["bitstamp_1_usdbtc"]

                price["bitstamp_1_eurbtc"] = Decimal(str(1/(last_price/Decimal(conversion_rate["sell"])))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
                update_btc_price("bitstamp_1_eurbtc", price["bitstamp_1_eurbtc"], datetime_updated)
                print "bitstamp_1_eurbtc: %s" % price["bitstamp_1_eurbtc"]

        elif exchange == "coinbase_btcusd":
            if u"btc" in response and u"subtotal" in response and "amount" in response["subtotal"]:
                print datetime.datetime.now()

                last_price = Decimal(response["subtotal"]["amount"])
                update_btc_price("coinbase_1_btcusd", last_price, datetime_updated)
                print "coinbase_1_btcusd: %s" % last_price

                price["coinbase_1_usdbtc"] = Decimal(str(1/(last_price))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
                update_btc_price("coinbase_1_usdbtc", price["coinbase_1_usdbtc"], datetime_updated)
                print "coinbase_1_usdbtc: %s" % price["coinbase_1_usdbtc"]

                price["coinbase_1_eurbtc"] = Decimal(str(1/(last_price/Decimal(conversion_rate)))).quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)
                update_btc_price("coinbase_1_eurbtc", price["coinbase_1_eurbtc"], datetime_updated)
                print "coinbase_1_eurbtc: %s" % price["coinbase_1_eurbtc"]
