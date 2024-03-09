import requests
import json
from time import sleep

WALLET = "MainTestnetWallet"

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
                timeout=45,
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

    def fund_address(self, address, amount):
        request = {
            "method": "sendtoaddress",
            "params": [address, amount],
        }
        return self._rpc(request, WALLET)

    def get_wallet_info(self):
        request = {
            "method": "getwalletinfo",
            "params": [],
        }
        return self._rpc(request, WALLET)

    def get_block_info(self):
        request = {
            "method": "getblockinfo",
            "params": [],
        }
        return self._rpc(request, WALLET)
        
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
