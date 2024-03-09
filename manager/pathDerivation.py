import os
os.environ['CRYPTOTOOLS_NETWORK'] = 'test'
os.environ['CRYPTOTOOLS_BACKEND'] = 'rpc'
os.environ['CRYPTOTOOLS_RPC_HOST'] = 'localhost'
os.environ['CRYPTOTOOLS_RPC_PORT'] = '18332'
os.environ['CRYPTOTOOLS_RPC_USER'] = 'TestnetUser1'
os.environ['CRYPTOTOOLS_RPC_PW'] = 'Testnet123'

from cryptos import *
from cryptotools.BTC import Xprv, Address
from manager import btc_node #USE WHEN RUNNING MANAGER1.PY
#import btc_node #USE WHEN RUNNING PATHDERVIATION.PY AS A SOLO APPLICATION.

node = btc_node.BtcNode()

def find_next_address(mnemonic, account_number):
    xprv = Xprv.from_mnemonic(mnemonic)
    key = xprv/84./1./0./0/account_number
    return key.address('P2WPKH')
    
def send_all_tbtc_back(mnemonic):
    xprv = Xprv.from_mnemonic(mnemonic)
    types = [0, 2147483645, 2147483646, 2147483644]
    for type in types:
        find_UTXO(xprv, type)

def find_UTXO(xprv, account_type):
    addresses = []
    keys_info = []
    
    for i in range(30):
        if account_type == 2147483645:
            key = xprv/84./1./2147483645./0/i
        elif account_type == 2147483646:
            key = xprv/84./1./2147483646./0/i
        elif account_type == 2147483644:
            key = xprv/84./1./2147483644./1/i
        elif account_type == 0:
            key = xprv/84./1./0./0/i

        child_private_key = key.key
        private_key_hex = child_private_key.hex()
        address = key.address('P2WPKH')
        
        addresses.append(address)
        keys_info.append((address, private_key_hex))
        print(f"Derived Address: {address}. Type {account_type} and Account: {i}")
        print(f"PrivateKey Hex: {private_key_hex}")
        
    utxos = node.check_utxos_for_address(addresses)

    for address, private_key_hex in keys_info:
        address_utxos = [utxo for utxo in utxos if f"addr({address})" in utxo.get('desc', '')]
        if not address_utxos:
            print(f"No UTXOs found for address {address}.")
            continue
        
        amount = sum(utxo['amount'] for utxo in address_utxos)
        amount_satoshis = int(amount * 100_000_000)
        print(f"Amount: {amount_satoshis} satoshis for address {address}")
        
        if amount_satoshis > 300:
            tx_hash = create_and_broadcast_tx(private_key_hex, address, "tb1qc0g63yf95g6kgz9dt960fdlsar0klfrnmz2qxs", amount_satoshis  - 300)
            print(f"Transaction Hash: {tx_hash}")
    
def create_and_broadcast_tx(private_key_hex, sender_address, recipient_address, amount_satoshis):
    c = Bitcoin(testnet=True)
    tx_hash = c.send(private_key_hex, sender_address, recipient_address, amount_satoshis, fee = 300)
    return tx_hash

#print(find_next_address("question present vague hill hunt guess assume soft innocent find sadness drum", 0))
#send_all_tbtc_back("joke auto multiply apology brown pipe ecology upgrade toast worth lemon middle")
#send_all_tbtc_back("grain inside execute tortoise echo sketch interest casino sign rally also please")
#send_all_tbtc_back("question present vague hill hunt guess assume soft innocent find sadness drum")