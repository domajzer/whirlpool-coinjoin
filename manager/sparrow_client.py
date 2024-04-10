class SparrowClient:
    def __init__(
        self, host="localhost", port=37128, name="whirlpool-sparrw-client", delay=0, proxy="", amount=None, address=None, mnemonic=None, account_number=0, connected=False, mixed=False
        ):
        self.host = host
        self.port = port
        self.name = name
        self.delay = delay
        self.proxy = proxy
        self.amount = amount
        self.address = address if address is not None else []
        self.mnemonic = mnemonic
        self.account_number = account_number
        self.connected = connected
        self.premix_mixed = mixed 
    
    @staticmethod
    def check_liquidity_premix_finish(clients):
        finished = 0
        for client in clients:
            if client.premix_mixed:
                finished += 1
        
        return finished == len(clients)