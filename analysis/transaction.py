class TxO:
    def __init__(self, address=None, value=0, inputVal=None):
        self.address = address
        self.value = value
        self.inputVal = inputVal

    def __str__(self):
        return f"TxO(address={self.address}, value={self.value}, inputVal={self.inputVal})"
