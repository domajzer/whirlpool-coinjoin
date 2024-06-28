class UserWallet:
    def __init__(self, inputs=None, transaction_ID=None, adresses=None, adresses_pairs=None, outputs=None, pairs=None, transactionID="", ip="", txo_path=None):
        self.inputs = inputs if inputs is not None else []
        self.transaction_ID = transaction_ID if transaction_ID is not None else []
        self.adresses_pairs = adresses_pairs if adresses_pairs is not None else {}
        self.outputs = outputs if outputs is not None else []
        self.pairs = pairs if pairs is not None else {}
        self.ip = ip
        self.txo_path = txo_path if txo_path is not None else []
    
    def __str__(self):
        return f"UserWallet(IP={self.ip}, inputs={self.inputs}, transaction_ID={self.transaction_ID}, adresses_pairs={self.adresses_pairs}, outputs={self.outputs}, pairs={self.pairs}, txo_path={self.txo_path}) \n"
