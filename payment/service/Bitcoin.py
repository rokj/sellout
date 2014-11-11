from bitcoinrpc.authproxy import AuthServiceProxy

class BitcoinRPC():
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

    def get_new_address(self, account):
        return self.access.getnewaddress(account)

    def get_received_by_address(self, address, minconf=1):
        return self.access.getreceivedbyaddress(address, minconf)

    def list_received_by_address(self, minconf=0, includeempty=False):
        return self.access.listreceivedbyaddress(minconf, includeempty)

    def get_transaction(self, txid):
        return self.access.gettransaction(txid)