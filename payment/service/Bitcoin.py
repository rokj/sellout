from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import settings
import logging

class BitcoinRPC():
    logger = logging.getLogger(__name__)

    def __init__(self, rpchost = None, rpcport = None, rpcuser = None, rpcpassword = None):
        self._rpchost = rpchost
        self._rpcport = rpcport
        self._rpcuser = rpcuser
        self._rpcpassword = rpcpassword

        self._access = AuthServiceProxy("http://%s:%s@%s:%s" % (self.rpcuser, self.rpcpassword, self.rpchost, self.rpcport))

    @property
    def access(self):
        return self._access

    @access.setter
    def access(self, value):
        self._access = value

    @access.deleter
    def access(self):
        del self._access

    @property
    def rpchost(self):
        return self._rpchost

    @rpchost.setter
    def rpchost(self, value):
        self._rpchost = value

    @rpchost.deleter
    def rpchost(self):
        del self._rpchost

    @property
    def rpcport(self):
        return self._rpcport

    @rpcport.setter
    def rpcport(self, value):
        self._rpcport = value

    @rpcport.deleter
    def rpcport(self):
        del self._rpcport

    @property
    def rpcuser(self):
        return self._rpcuser

    @rpcuser.setter
    def rpcuser(self, value):
        self._rpcuser = value

    @rpcuser.deleter
    def rpcuser(self):
        del self._rpcuser

    @property
    def rpcpassword(self):
        return self._rpcpassword

    @rpcpassword.setter
    def rpcpassword(self, value):
        self._rpcpassword = value

    @rpcpassword.deleter
    def rpcpassword(self):
        del self._rpcpassword

    def increase_keypool_size(self):
        try:
            self.access.walletpassphrase(settings.PAYMENT['bitcoin']['walletpassphrase'], settings.PAYMENT['bitcoin']['walletpassphrase_timeout'])
            self.access.keypoolrefill()
            self.logger.info("Just refilled bitcoin keypool size.")
        except JSONRPCException, e:
            print str(e.error.message)

            self.logger.error("Could not increase bitcoin keypool size.")

    def check_keypool_size(self):
        try:
            info = self.access.getinfo()

            if info and 'keypoolsize' in info:
                if int(info['keypoolsize']) < settings.PAYMENT['bitcoin'] ['minimum_keypoolsize']:
                    self.increase_keypool_size()



        except JSONRPCException, e:
            print str(e.error.message)

    def get_new_address(self, account):
        address = ""

        self.check_keypool_size()

        try:
            address = self.access.getnewaddress(account)
        except JSONRPCException, e:
            print str(e.error.message)

        return address

    def get_received_by_address(self, address, minconf=1):
        return self.access.getreceivedbyaddress(address, minconf)

    def list_received_by_address(self, minconf=0, includeempty=False):
        return self.access.listreceivedbyaddress(minconf, includeempty)

    def get_transaction(self, txid):
        return self.access.gettransaction(txid)

    def list_since_block(self, blockhash=""):
        if blockhash == "":
            return self.access.listsinceblock()

        return self.access.listsinceblock(blockhash)
