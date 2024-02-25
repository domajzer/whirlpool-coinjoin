import os
os.environ['CRYPTOTOOLS_NETWORK'] = 'test'
os.environ['CRYPTOTOOLS_BACKEND'] = 'rpc'
os.environ['CRYPTOTOOLS_RPC_HOST'] = 'localhost'
os.environ['CRYPTOTOOLS_RPC_PORT'] = '18332'
os.environ['CRYPTOTOOLS_RPC_USER'] = 'TestnetUser1'
os.environ['CRYPTOTOOLS_RPC_PW'] = 'Testnet123'

from cryptos import *
from cryptotools.BTC import Xprv, Address

def send_all_tbtc_back(mnemonic):
    xprv = Xprv.from_mnemonic(mnemonic)
    types = [0, 2147483645, 2147483646, 2147483644]
    for type in types:
        find_UTXO(xprv, type)

def find_UTXO(xprv, account_type):
    for i in range(25):
        if account_type == 2147483645:
            key = xprv/84./1./2147483645./0/i
        elif account_type == 2147483646:
            key = xprv/84./1./2147483646./0/i
        elif account_type == 2147483644:
            key = xprv/84./1./2147483644./0/i
        elif account_type == 0:
            key = xprv/84./1./0./0/i

        child_private_key = key.key
        private_key_hex = child_private_key.hex()
        address = key.address('P2WPKH')
        
        print(f"Derived Address: {address}. Type {account_type} and Account: {i}")
        print(f"PrivateKey Hex: {private_key_hex}")
        test_address = Address(address)
        amount = test_address.balance()
        amount = (int(amount * 100_000_000))
        print(amount)
        if amount > 0:
            tx_hash = create_and_broadcast_tx(private_key_hex, address, "tb1qgvjp9dnyl3wul23jhq84q7zn6068dekh8e604e", amount - 300)
            print(f"Transaction Hash: {tx_hash}")
    
def create_and_broadcast_tx(private_key_hex, sender_address, recipient_address, amount_satoshis):
    c = Bitcoin(testnet=True)
    tx_hash = c.send(private_key_hex, sender_address, recipient_address, amount_satoshis, fee = 300)
    return tx_hash
