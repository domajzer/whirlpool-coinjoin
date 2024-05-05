class UserWallet:
    def __init__(self, inputs=None, transaction_path=None, adresses=None, adresses_pairs=None, outputs=None, pairs=None, transactionID="", ip=""):
        self.inputs = inputs if inputs is not None else []
        self.transaction_path = transaction_path if transaction_path is not None else []
        self.adresses_pairs = adresses_pairs if adresses_pairs is not None else {}
        self.outputs = outputs if outputs is not None else []
        self.pairs = pairs if pairs is not None else {}
        self.ip = ip