import os
import time
os.environ['CRYPTOTOOLS_NETWORK'] = 'test'
os.environ['CRYPTOTOOLS_BACKEND'] = 'rpc'
os.environ['CRYPTOTOOLS_RPC_HOST'] = 'localhost'
os.environ['CRYPTOTOOLS_RPC_PORT'] = '18332'
os.environ['CRYPTOTOOLS_RPC_USER'] = 'TestnetUser1'
os.environ['CRYPTOTOOLS_RPC_PW'] = 'Testnet123'

from cryptos import *
from cryptotools.BTC import Xprv, Address
#from manager import btc_node #USE WHEN RUNNING MANAGER1.PY
import btc_node #USE WHEN RUNNING PATHDERVIATION.PY AS A SOLO APPLICATION.

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
            tx_hash = create_and_broadcast_tx(private_key_hex, address, "tb1qvm88fe9dzjdvesdsg5njg83gds7quqspxnprw3", amount_satoshis  - 300, 5)
            print(f"Transaction Hash: {tx_hash}")
            time.sleep(5)
    
def create_and_broadcast_tx(private_key_hex, sender_address, recipient_address, amount_satoshis, max_attempts):
    c = Bitcoin(testnet=True)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            tx_hash = c.send(private_key_hex, sender_address, recipient_address, amount_satoshis, fee=300)
            print(f"Transaction sent successfully. Hash: {tx_hash}")
            return tx_hash
        
        except Exception as e: 
            print(f"Transaction failed due to timeout. Attempt {attempt + 1} of {max_attempts}. Retrying in 15 seconds...")
            time.sleep(15)
            attempt += 1
        
    if attempt == max_attempts:
        print("Max attempts reached. Transaction not sent.")
        return None 
def open_seed_and_sendtbtc():
    with open("seed", 'r') as file:
        for line in file:
            cleaned_line = line.strip()
            print(cleaned_line)
            send_all_tbtc_back(cleaned_line)
