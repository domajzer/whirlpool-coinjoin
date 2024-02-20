#!/usr/bin/env python3.10

from manager.btc_node import BtcNode
from manager.sparrow_client import SparrowClient
#from manager import utils
from time import sleep, time
import random
import os
import re
import threading
import datetime
import json
import argparse
import shutil
import tempfile
import multiprocessing


BTC = 100_000_000
SCENARIO = {
    "name": "default",
    "rounds": 10,  # the number of coinjoins after which the simulation stops (0 for no limit)
    "blocks": 0,  # the number of mined blocks after which the simulation stops (0 for no limit)
    "liquidity-wallets": [
        {"funds": [200000, 50000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},     
    ],
    "wallets": [
        {"funds": [200000, 50000], "delay": 0},
        {"funds": [3000000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [3000000, 15000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
        {"funds": [3000000, 600000], "delay": 0},
        {"funds": [1000000, 500000], "delay": 0},
    ],
}

args = None
driver = None
node = None
coordinator = None
distributor = None
clients = []
premix_check = 0
shutdown_event = threading.Event()

def prepare_image(name):
    prefixed_name = args.image_prefix + name
    if driver.has_image(prefixed_name):
        if args.force_rebuild:
            if args.image_prefix:
                driver.pull(prefixed_name)
                print(f"- image pulled {prefixed_name}")
            else:
                driver.build(name, f"./containers/{name}")
                print(f"- image rebuilt {prefixed_name}")
        else:
            print(f"- image reused {prefixed_name}")
    elif args.image_prefix:
        driver.pull(prefixed_name)
        print(f"- image pulled {prefixed_name}")
    else:
        driver.build(name, f"./containers/{name}")
        print(f"- image built {prefixed_name}")


def prepare_images():
    print("Preparing images")
    prepare_image("bitcoin-testnet-node")
    prepare_image("whirlpool-db")
    prepare_image("whirlpool-db-init")
    prepare_image("whirlpool-server")
    prepare_image("whirlpool-sparrow-client")

def start_infrastructure():
        
    print("Starting infrastructure")
    testnet3_path = os.path.abspath("/home/domajzer/coinjoin-simulator-main/btc-docker/testnet3")
    btc_node_ip, btc_node_ports = driver.run(
        "bitcoin-testnet-node",
        "bitcoin-testnet-node",
        ports={'18332/tcp': 18332},
        cpu=2.0,
        memory=3072,
        volumes={testnet3_path: {'bind': '/home/bitcoin/.bitcoin/testnet3', 'mode': 'rw'}}
    )
    global node
    node = BtcNode(
        host="localhost",
        port=18332,
        rpc_user="TestnetUser1",
        rpc_password="Testnet123"
    )
    #node.wait_ready()
    print("- started btc-node")

    whirlpool_db_ip, whirlpool_db_ports = driver.run(
        "whirlpool-db",
        f"{args.image_prefix}whirlpool-db",
        ports={'3306/tcp': 3307},
        env={'MYSQL_ROOT_PASSWORD': 'root', 'MYSQL_DATABASE': 'whirlpool_testnet'},
        cpu=0.8,
        memory=1024,
        volumes={"whirlpool-db": {'bind': '/var/lib/mysql', 'mode': 'rw'}}
    )
    print("- started whirlpool-db")
    
    whirlpool_db_python_ip, whirlpool_db_python_ports = driver.run(
        "whirlpool-db-init",
        f"{args.image_prefix}whirlpool-db-init",
        env={'MYSQL_ROOT_PASSWORD': 'root'}
    )
    sleep(10)
    print("- started whirlpool-db-init")
    global whirlpool_server_ip
    whirlpool_server_ip, whirlpool_server_ports = driver.run(
        "whirlpool-server",
        f"{args.image_prefix}whirlpool-server",
        ports={'8080/tcp': 8080},
        cpu=1.0,
        memory=2048,
    )
    sleep(60)
    print("- started coordinator")

def start_client(idx, wallet):
    sleep(random.random() * 3)
    name = f"whirlpool-sparrow-client-{idx:03}"
    try:
        ip, manager_ports = driver.run(
            name,
            f"{args.image_prefix}whirlpool-sparrow-client",
            ports={37128: 37129 + idx},
            tty=True
        )
        
        client = SparrowClient(
            host=ip if args.proxy else args.control_ip,
            port=37128 if args.proxy else manager_ports[37128],
            name=name,
            delay=wallet.get("delay", 0),
            proxy=args.proxy,
        )
        sleep(15)
        
        if not driver.setup_socat_in_container(name, whirlpool_server_ip):
            print(f"Failed to setup socat for {name}")
            return None
        
    except Exception as e:
        print(f"- could not start {name} ({e})")
        return None
    
    return client

def start_clients(wallets):
    print("Starting clients")
    with multiprocessing.Pool() as pool:
        new_clients = pool.starmap(start_client, enumerate(wallets, start=len(clients)))
        print(enumerate(wallets, start=len(clients)))
        
        successfully_started_clients = [client for client in new_clients if client is not None]

        clients.extend(new_clients)
        print(f"Successfully started {len(successfully_started_clients)} clients.")

def capture_logs_periodically(clients, btc_node, premix_matched_containers, interval=55):
    global premix_check
    if shutdown_event.is_set():
        return
    
    for client in clients:
        sleep(2)
        driver.capture_and_save_logs(client, f"whirlpool-sparrow-client/logs/{client.name}.txt")
        if parse_address_send_btc(client, f"whirlpool-sparrow-client/logs/{client.name}.txt") and (premix_check == 0):
            premix_matched_containers.add(client)
            print(f"Container {client.name} has finished mixing premix UTXO.")
            
    if (premix_matched_containers == set(clients)) and (premix_check == 0):
        driver.upload("whirlpool-server", "stopfile", "whirlpool-server:/app/stopfile")
        premix_check = 1

    send_btc("whirlpool-sparrow-client/tmp/addresses.txt","whirlpool-sparrow-client/tmp/addresses_send.txt", client, btc_node)
    
    if not shutdown_event.is_set():
        timer = threading.Timer(interval, capture_logs_periodically, [clients, btc_node, premix_matched_containers,interval])
        timer.start()

def parse_address_send_btc(client, log_file_path):
    tbtc_address_pattern = r'\$\$Wallet\$\$Address\$\$: (tb1[a-z0-9]{39,59})'
    premix_UTXO_mixed_pattern = r'All [0-9]{1,4} UTXOs have been mixed'
    output_file_path = "whirlpool-sparrow-client/tmp/addresses.txt"
    pattern_found = False
    
    try:
        with open(log_file_path, 'r') as file:
            addresses_in_file = set()

            if os.path.exists(output_file_path):
                with open(output_file_path, 'r') as file2:
                    addresses_in_file = set(line.strip() for line in file2)

            for line in file:
                match = re.search(tbtc_address_pattern, line)
                if match:
                    tbtc_address = match.group(1)
                    
                    if tbtc_address not in client.address:
                        with open(output_file_path, 'a') as file2:
                            file2.write(tbtc_address + '\n')
                            addresses_in_file.add(tbtc_address)
                            client.address = tbtc_address
                            
                if re.search(premix_UTXO_mixed_pattern, line):
                    pattern_found = True
                      
    except FileNotFoundError:
        print(f"Log file {log_file_path} not found")
    
    return pattern_found

def send_btc(output_path, client, btc_node):
    try:
        if client.address and client.amount > 0:
            with open(output_path, 'r') as output_file:
                sent_addresses = set(output_file.read().splitlines())
        
        if client.address not in sent_addresses:
            with open(output_path, 'a') as output_file:
                try:
                    transaction_info = btc_node.fund_address(client.address, client.amount)
                    output_file.write(client.address + '\n')
                    print("Transaction info:", transaction_info)

                except Exception as e:
                    print(f"Error sending BTC to {client.address}: {e}")
             
    except Exception as e:
        print(f"Error in send_btc: {e}")

def run():
    if args.scenario:
        with open(args.scenario) as f:
            SCENARIO.update(json.load(f))

    try:
        print(f"=== Scenario {SCENARIO['name']} ===")
        premix_matched_containers = set()
        
        prepare_images()
        start_infrastructure()
        #wallet_config = SCENARIO["liquidity-wallets"][0]
        #client_name = start_client(1, wallet_config)
        #fund_distributor(1000)
        start_clients(SCENARIO["liquidity-wallets"])
        capture_logs_periodically(clients, node, premix_matched_containers)
        
        while(premix_check == 0):
            print("Waiting for the liquidity mix to finish")
            sleep(60)
            
        print("Changing coordinator config")
        start_clients(SCENARIO["wallets"])

        """
        invoices = [
            (client, wallet.get("funds", []))
            for client, wallet in zip(clients, SCENARIO["wallets"])
        ]
        fund_clients(invoices)

        print("Mixing")
        rounds = 0
        initial_blocks = node.get_block_count()
        blocks = 0
        while (SCENARIO["rounds"] == 0 or rounds < SCENARIO["rounds"]) and (
            SCENARIO["blocks"] == 0 or blocks < SCENARIO["blocks"]
        ):
            for _ in range(3):
                try:
                    rounds = sum(
                        1
                        for _ in driver.peek(
                            "wasabi-backend",
                            "/home/wasabi/.walletwasabi/backend/WabiSabi/CoinJoinIdStore.txt",
                        ).split("\n")[:-1]
                    )
                    break
                except Exception as e:
                    print(f"- could not get rounds ({e})")
                    rounds = 0

            start_coinjoins(blocks := node.get_block_count() - initial_blocks)
            print(f"- coinjoin rounds: {rounds} (block {blocks})", end="\r")
            sleep(1)
        print()
        print(f"- limit reached")
        """
    except KeyboardInterrupt:
        print()
        print("KeyboardInterrupt received")
    finally:
        #stop_coinjoins()
        #if not args.no_logs:
            #store_logs()
        #driver.cleanup(args.image_prefix)
        print('A')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run coinjoin simulation setup")
    parser.add_argument("command", type=str, choices=["build", "clean", "run"])
    parser.add_argument("--image-prefix", type=str, default="", help="image prefix")
    parser.add_argument(
        "--force-rebuild", action="store_true", help="force rebuild of images"
    )
    parser.add_argument("--scenario", type=str, help="scenario specification")
    parser.add_argument(
        "--driver",
        type=str,
        choices=["docker", "podman", "kubernetes"],
        default="docker",
    )
    parser.add_argument(
        "--btc-node-ip", type=str, help="override btc-node ip", default=""
    )
    parser.add_argument(
        "--wasabi-backend-ip",
        type=str,
        help="override wasabi-backend ip",
        default="",
    )
    parser.add_argument(
        "--control-ip", type=str, help="control ip", default="localhost"
    )
    parser.add_argument("--namespace", type=str, default="coinjoin")
    parser.add_argument("--reuse-namespace", action="store_true", default=False)
    parser.add_argument("--no-logs", action="store_true", default=False)
    parser.add_argument("--proxy", type=str, default="")

    args = parser.parse_args()

    match args.driver:
        case "docker":
            from manager.driver.docker import DockerDriver

            driver = DockerDriver(args.namespace)
        case "kubernetes":
            from manager.driver.kubernetes import KubernetesDriver

            driver = KubernetesDriver(args.namespace, args.reuse_namespace)
        case _:
            print(f"Unknown driver '{args.driver}'")
            exit(1)

    match args.command:
        case "build":
            prepare_images()
        case "clean":
            driver.cleanup(args.image_prefix)
        case "run":
            run()
        case _:
            print(f"Unknown command '{args.command}'")
            exit(1)
