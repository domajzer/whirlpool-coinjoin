class Mix:
    def __init__(self, inputs=None, input_pair=None, mix_ips=None, outputs=None, output_pair=None, pairs=None, transactionID="", anonSet=0, premixSet=0, postmixSet=0, fees=0):
        self.inputs = inputs if inputs is not None else []
        self.input_pair = input_pair if input_pair is not None else []
        self.mix_ips = mix_ips if mix_ips is not None else []
        self.outputs = outputs if outputs is not None else []
        self.output_pair = output_pair if output_pair is not None else []
        self.pairs = pairs if pairs is not None else {}
        self.transactionID = transactionID
        self.anonSet = anonSet
        self.premixSet = premixSet
        self.postmixSet = postmixSet
        self.fees = fees
    