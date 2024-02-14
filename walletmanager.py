import requests
import json
from time import sleep

WALLET = "MainTestnetWallet"

class BtcNode:
    def __init__(self, host="bitcoin-testnet-node", port=18332, rpc_user="TestnetUser1", rpc_password="Testnet123", internal_ip="", proxy=""):
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
                timeout=5,
            )
        except requests.exceptions.Timeout:
            return "timeout"
        if response.json()["error"] is not None:
            raise Exception(response.json()["error"])
        return response.json()["result"]

    def fund_address(self, address, amount):
        request = {
            "method": "sendtoaddress",
            "params": [address, amount],
        }
        self._rpc(request, WALLET)

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
