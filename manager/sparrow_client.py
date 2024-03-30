
class SparrowClient:
    def __init__(
        self, host="localhost", port=37128, name="whirlpool-sparrw-client", delay=0, proxy="", amount=None, address=[], mnemonic=None, account_number=0, connected=False, mixed=False
        ):
        self.host = host
        self.port = port
        self.name = name
        self.delay = delay
        self.amount = amount
        self.address = address
        self.mnemonic = mnemonic
        self.account_number = account_number
        self.connected = connected
        self.premix_mixed = mixed 