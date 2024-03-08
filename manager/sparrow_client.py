
class SparrowClient:
    def __init__(
        self, host="localhost", port=37128, name="whirlpool-sparrw-client", delay=0, proxy="", amount=None, address=None, mneumonic=""
    ):
        self.host = host
        self.port = port
        self.name = name
        self.delay = delay
        self.proxy = proxy
        self.amount = amount
        self.address = address
        self.mnemonic = mneumonic