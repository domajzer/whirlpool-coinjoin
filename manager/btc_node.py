import requests
import json
from time import sleep

WALLET = "wallet"

class BtcNode:
    def __init__(self, host="localhost", port=18332, rpc_user="TestnetUser1", rpc_password="Testnet123", internal_ip="", proxy=""):
        self.host = host
        self.port = port
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.internal_ip = internal_ip
        self.proxy = proxy

    def _rpc(self, request, wallet=None):
        request["jsonrpc"] = "2.0"
        request["id"] = "1"
        try:
            response = requests.post(
                f"http://{self.host}:{self.port}"
                + ("/wallet/" + WALLET if wallet else ""),
                data=json.dumps(request),
                auth=(self.rpc_user, self.rpc_password),
                proxies=dict(http=self.proxy),
                timeout=60,
            )
        except requests.exceptions.Timeout:
            return "timeout"
        
        if response.json()["error"] is not None:
            raise Exception(response.json()["error"])
        return response.json()["result"]

    def check_utxos_for_address(self, addresses):
        request = {
            "method": "scantxoutset",
            "params": ["start", [f"addr({address})" for address in addresses]],
        }
        
        response = self._rpc(request)
        
        if response and 'success' in response and response['success']:
            if 'unspents' in response and response['unspents']:
                return response['unspents']
            
            else:
                print(f"UTXOs found but 'unspents' list is empty for addresses: {addresses}")
                return []
            
        else:
            print(f"Failed to get UTXOs for {addresses} or no UTXOs found.")
            return []

    def fund_address(self, address, amount, conf_target=1, estimate_mode='ECONOMICAL'):
        request = {
            "method": "sendtoaddress",
            "params": [address, amount, "", "", False, False, conf_target, estimate_mode],
        }
        return self._rpc(request, WALLET)
    
    def import_private_key(self, wif_key, label=""):
        request = {
        "method": "importprivkey",
        "params": [wif_key, label, True], 
        }
        return self._rpc(request, WALLET)
        
    def get_wallet_info(self):
        request = {
            "method": "getwalletinfo",
            "params": [],
        }
        return self._rpc(request, WALLET)
    
    def wait_for_wallet_ready(self):
        print("Waiting for wallet to be ready...")
        
        while True:
            try: 
                wallet_info = self.get_wallet_info()
                if "scanning" not in wallet_info or wallet_info["scanning"] is False:
                    print("Wallet is ready.")
                    break
            
                else:
                    print("Wallet is still scanning the blockchain. Waiting...")
                    sleep(10)
            except Exception as e:
                print(f"Unkown wallet {e}")
                
            sleep(10)
        
    def get_block_count(self):
        request = {
            "method": "getblockcount",
            "params": [],
        }
        return self._rpc(request)
        
    def load_wallet(self):
        request = {
            "method": "loadwallet",
            "params": [WALLET],
        }
        return self._rpc(request, WALLET)
    
    def get_blockchain_info(self):
        request = {
            "method": "getblockchaininfo",
            "params": [],
        }
        return self._rpc(request)
    
    def wait_ready(self):
        print("Waiting for the node to be fully synchronized with the network...")
        while True:
            try:
                blockchain_info = self.get_blockchain_info()
                verification_progress = blockchain_info.get('verificationprogress', 0)
                print(f"Current verification progress: {verification_progress * 100:.2f}%")
                
                if verification_progress >= 0.9999:
                    print("The node is synchronized.")
                    break
                
            except Exception as e:
                print(f"Error checking node synchronization status: {e}")
            sleep(10)
            
    def wait_for_new_block(self):
        response = self.get_blockchain_info()
        initial_block = response["blocks"]
        
        while True:
            response = self.get_blockchain_info()
            new_block = response["blocks"]
            
            if new_block > initial_block:
                print(f"New block found: {new_block}")
                break
            
            print("Waiting for a new block...")
            sleep(30)
