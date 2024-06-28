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
    
    def __str__(self):
        inputs_str = ", ".join(str(input) for input in self.inputs)
        outputs_str = ", ".join(str(output) for output in self.outputs)
        return (f"Mix(transactionID={self.transactionID}, anonSet={self.anonSet}, premixSet={self.premixSet}, "
                f"postmixSet={self.postmixSet}, fees={self.fees}, inputs=[{inputs_str}], input_pair={self.input_pair}, "
                f"mix_ips={self.mix_ips}, outputs=[{outputs_str}], output_pair={self.output_pair}, pairs={self.pairs}) \n")
