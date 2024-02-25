import os
os.environ['CRYPTOTOOLS_NETWORK'] = 'test'
os.environ['CRYPTOTOOLS_BACKEND'] = 'rpc'
os.environ['CRYPTOTOOLS_RPC_HOST'] = 'localhost'
os.environ['CRYPTOTOOLS_RPC_PORT'] = '18332'
os.environ['CRYPTOTOOLS_RPC_USER'] = 'TestnetUser1'
os.environ['CRYPTOTOOLS_RPC_PW'] = 'Testnet123'

from cryptos import *
from cryptotools.BTC import Xprv, Address

def find_UTXO(mnemonic):
    xprv = Xprv.from_mnemonic(mnemonic)
    for i in range(1):
        key = xprv/84./1./2147483645./0/54
        child_private_key = key.key
        private_key_hex = child_private_key.hex()
        address = key.address('P2WPKH')
        
        print(f"Derived Address: {address}")
        print(private_key_hex)
        test_address = Address(address)
        amount = test_address.balance()
        amount = (int(amount * 100_000_000) - 300)
        print(amount)
        if amount > 0:
            tx_hash = create_and_broadcast_tx(private_key_hex, address, "tb1qgvjp9dnyl3wul23jhq84q7zn6068dekh8e604e", amount)
            print(tx_hash)
    
def create_and_broadcast_tx(private_key_hex, sender_address, recipient_address, amount_satoshis):
    c = Bitcoin(testnet=True)
    tx_hash = c.send(private_key_hex, sender_address, recipient_address, amount_satoshis, fee = 300)
    return tx_hash

mnemonic = "series upon match cover skill silly flavor zebra dilemma bar solid finish"

find_UTXO(mnemonic)