#!/usr/bin/env python3.10

from manager.btc_node import BtcNode
from manager.sparrow_client import SparrowClient
from time import sleep, time
from manager import utils
import manager.pathDerivation 
import os
import re
import json
import argparse
from threading import Thread, Event, Timer

BTC = 100_000_000
SCENARIO = {
    "name": "default",
    "rounds": 10,  # the number of coinjoins after which the simulation stops (0 for no limit)
    "blocks": 0,  # the number of mined blocks after which the simulation stops (0 for no limit)
    "liquidity-wallets": [
        {"funds": [8000,6000,6000], "delay": 0},
        {"funds": [7000,6000], "delay": 0},
        {"funds": [8000], "delay": 0},
    ],
    "wallets": [
        {"funds": [9000], "delay": 60},
        {"funds": [9000,7000], "delay": 120},
    ],
}

args = None
driver = None
node = None
coordinator = None
finish_check = 0
clients = []
shutdown_event = Event()
global_idx = 0

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
    prepare_image("whirlpool-server")
    prepare_image("whirlpool-sparrow-client")

def start_infrastructure():
    
    if args.driver == "kubernetes":
        try:
            driver.create_persistent_volume_claim(pvc_name="testnet-chain", storage_size=50) #STORAGE SIZE IN GI
        except:
            print("PVC arelady created")
        volume = {"testnet-chain": "/home/bitcoin/.bitcoin/testnet3"}
        print("Kubernetes infrastructure is being started.")
    elif args.driver == "docker":
        testnet3_path = os.path.abspath("containers/bitcoin-testnet-node/testnet3")
        volume = {testnet3_path: {'bind': '/home/bitcoin/.bitcoin/testnet3', 'mode': 'rw'}}
        print("Docker infrastructure is being started.")

    print("Starting infrastructure")
    btc_node_ip, btc_node_ports = driver.run(
        "bitcoin-testnet-node",
        f"{args.image_prefix}bitcoin-testnet-node",
        ports={18332: 18332},
        cpu=6.4,
        memory=5520,
        volumes=volume
    )
    print(btc_node_ip)
    global node
    node = BtcNode(
        host=btc_node_ip if args.proxy else args.control_ip,
        port=18332 if args.proxy else btc_node_ports[18332],
        rpc_user="TestnetUser1",
        rpc_password="Testnet123",
        internal_ip=btc_node_ip
    )
    print("- started btc-node")

    whirlpool_db_ip, whirlpool_db_ports = driver.run(
        "whirlpool-db",
        f"{args.image_prefix}whirlpool-db",
        ports={3306: 3307},
        env={'MYSQL_ROOT_PASSWORD': 'root', 'MYSQL_DATABASE': 'whirlpool_testnet'},
        cpu=1.4,
        memory=1024
    )
    
    node.wait_ready()
    if args.wif:
        try:
            node.import_private_key(args.wif)
            node.wait_for_wallet_ready()
            
        finally:
            args.wif = " " * len(args.wif)
            del args.wif
            
    if args.wallet:
        driver.upload("bitcoin-testnet-node", args.wallet, "home/bitcoin/.bitcoin/testnet3/wallets")
        sleep(30)
        
    print(node.load_wallet())
    node.wait_for_wallet_ready()
    print(node.get_wallet_info())
    print(node.get_block_count())
    
    print("- started whirlpool-db")
    sleep(20)
    global whirlpool_server_ports
    whirlpool_server_ip, whirlpool_server_ports = driver.run(
        "whirlpool-server",
        f"{args.image_prefix}whirlpool-server",
        ports={8080: 8080},
        cpu=2.5,
        memory=2048
    )
    sleep(30)
    if args.driver == "kubernetes":
        custom_properties_path = utils.update_coordinator_config(
                                    "containers/whirlpool-coordinator/custom.properties",
                                    whirlpool_db_ip,
                                    btc_node_ip,
                                    "logs")
        
    elif args.driver == "docker":
        custom_properties_path = "containers/whirlpool-coordinator/custom.properties"
    
    driver.upload("whirlpool-server", custom_properties_path, "/app/whirlpool-server/config.properties")
    sleep(30)
    print("- started coordinator")

def start_client(idx, wallet, client_name, config_path):
    sleep(wallet.get("delay", 20 * idx))
    name = f"whirlpool-{client_name}-{idx:03}"
    
    if args.driver == "docker":
        cmd = f"python3 /usr/src/app/automation.py -debugf -mix -pool -create -name {name}"
        
    else: 
        cmd = ["/bin/sh", "-c", f"python3 /usr/src/app/automation.py -debugf -mix -pool -create -name {name}"]
        
    try:
        ip, manager_ports = driver.run(
            name,
            f"{args.image_prefix}whirlpool-sparrow-client",
            ports={37128: 37129 + idx},
            tty=True,
            command=cmd,
            cpu=1.1,
            memory=1024,
        )
        funds_btc = [fund / BTC for fund in wallet.get("funds", [])]
        
        client = SparrowClient(
            host=ip if args.proxy else args.control_ip,
            port=37128 if args.proxy else manager_ports[37128],
            name=name,
            delay=wallet.get("delay", 20),
            proxy=args.proxy,
            amount=funds_btc
        )
        sleep(3)
        driver.upload(name , config_path, "/usr/src/app/.sparrow/testnet/config")
        if not driver.setup_socat_in_container(name, driver.get_container_ip("whirlpool-server"), 8080):
            print(f"Failed to setup socat for {name}")
            return None
        
    except Exception as e:
        print(f"- could not start {name} ({e})")
        return None
    
    return client

def start_clients(wallets, name):
    global global_idx, clients
    print("Starting clients")
    batch_size = 5 
    if args.driver == "kubernetes":
        config_path = utils.update_client_config("containers/whirlpool-sparrow-client/config", node.internal_ip, "logs")
            
    elif args.driver == "docker":
        config_path = "containers/whirlpool-sparrow-client/config"
    
    for i in range(0, len(wallets), batch_size):
        current_batch_clients = []
        current_batch = wallets[i:i+batch_size]

        for idx, wallet in enumerate(current_batch):
            client_index = global_idx + idx 
            client = start_client(client_index, wallet, name, config_path)
            
            if client:
                current_batch_clients.append(client)
                clients.append(client)
                print(f"Started client {client.name}.")
                
            else:
                print(f"Failed to start client for wallet index {client_index}.")

        all_connected = True
        for client in current_batch_clients:
            if not wait_for_client_to_connect(client):
                all_connected = False
                print(f"Client {client.name} failed to connect.")
                break

        if all_connected:
            print("All clients in the current batch connected successfully. Proceeding with the next batch.")
            
        else:
            print("Not all clients in the current batch connected successfully. Stopping.")
            break 

        global_idx += len(current_batch)

    print(f"Successfully started and processed {len(clients)} clients out of {len(wallets)}.")

def wait_for_client_to_connect(client, max_attempts=85, attempt_delay=10):
    pattern = "Wallet successfully connected to bitcoin node."
    attempts = 0
    
    while attempts < max_attempts:
        try:
            driver.capture_and_save_logs(client,f"logs/{client.name}.txt")
            sleep(2)
            
            with open(f"logs/{client.name}.txt", 'r') as file:
                for line in file:
                    if pattern in line:
                        print(f"Client {client.name} successfully connected. {line}")
                        client.connected = True
                        return True
                    
        except FileNotFoundError:
            print(f"Attempt {attempts + 1}: Log file for {client.name} not found.")

        attempts += 1
        sleep(attempt_delay)
    
    print(f"Failed to confirm connection for {client.name} after {max_attempts} attempts.")
    return False
    
def parse_address_and_mnemonic(client, log_file_path):
    premix_UTXO_mixed_pattern = r'All [0-9]{1,4} UTXOs have been mixed'
    mnemonic_pattern = r'Seed words: ((?:[a-z]+ ){11}[a-z]+)'     
    try:
        with open(log_file_path, 'r') as file:

            for line in file:      
                match_mnemonic = re.search(mnemonic_pattern, line)
                
                if match_mnemonic:
                    if client.mnemonic is None:
                        with open("seed", 'a+') as seed:
                            seed.write(match_mnemonic.group(1) + '\n')
                            
                    client.mnemonic = match_mnemonic.group(1)
                                        
                if re.search(premix_UTXO_mixed_pattern, line):
                    client.premix_mixed = True
                    
    except FileNotFoundError:
        print(f"Log file {log_file_path} not found")
    
    return client.premix_mixed
    
def send_btc(client, btc_node):
    try:
        if client.amount and (len(client.amount) != client.account_number) and (client.mnemonic is not None):
            for amount in client.amount:
                if amount > 0:
                    try:
                        client.address.append(manager.pathDerivation.find_next_address(client.mnemonic, client.account_number))
                        transaction_info = btc_node.fund_address(client.address[client.account_number], amount)
                        
                        print("Transaction info:", transaction_info)
                        client.account_number += 1

                    except Exception as e:
                        print(f"Error sending BTC to {client.address}: {e}")
                                                
                else:
                    raise ValueError(f"Error sending BTC to {client.address}: Not valid amount: {amount}")
             
    except Exception as e:
        print(f"Error in send_btc: {e}")
     
def capture_logs_for_group(group_clients, btc_node, interval=45):
    print(f"Collecting logs for {group_clients}")

    while not shutdown_event.is_set():
        for client in group_clients:
            driver.capture_and_save_logs(client, f"logs/{client.name}.txt")
            sleep(2)
            
            if client.mnemonic is None or client.premix_mixed is False:
                if parse_address_and_mnemonic(client, f"logs/{client.name}.txt"):
                    print(f"Container {client.name} has finished mixing premix UTXO.")
            
            send_btc(client, btc_node)
        
        sleep(interval)

def start_log_capture_in_threads(clients, btc_node, interval=45, group_size=20):
    threads = []
    client_groups = [clients[i:i + group_size] for i in range(0, len(clients), group_size)]
    
    for group in client_groups:
        t = Thread(target=capture_logs_for_group, args=(group, btc_node, interval))
        threads.append(t)
        t.start()

    return threads

def stop_log_capture_threads(threads):
    shutdown_event.set()
    for t in threads:
        t.join()

def run():
    if args.scenario:
        with open(args.scenario) as f:
            SCENARIO.update(json.load(f))

    try:
        print(f"=== Scenario {SCENARIO['name']} ===")
        
        prepare_images()
        start_infrastructure()
        
        start_clients(SCENARIO["liquidity-wallets"], "liquidity-wallets")
        threads = start_log_capture_in_threads(clients, node)
        
        while not SparrowClient.check_liquidity_premix_finish(clients):
            print("Waiting for the liquidity mix to finish")
            sleep(60)
            
        print("Changing coordinator config")    
        driver.upload("whirlpool-server", "stopfile", "/app/stopfile")
        sleep(30)

        stop_log_capture_threads(threads)
        shutdown_event.clear()
        sleep(30)
            
        start_clients(SCENARIO["wallets"], "wallets")
        initial_block = node.get_block_count()
        new_threads = start_log_capture_in_threads(clients, node)
            
        while (SCENARIO["blocks"] == 0 or (node.get_block_count() - initial_block) < SCENARIO["blocks"]) and not SparrowClient.check_liquidity_premix_finish(clients):
            print("COLLECING LOGS FROM WHIRLPOOL-SERVER")
            driver.download("whirlpool-server", "/app/logs/mixs.csv", "logs")
            driver.download("whirlpool-server", "/app/logs/activity.csv", "logs")
            sleep(45)
            
        print("ALL WALLETS HAVE FINISHED MIXING.....")

    except KeyboardInterrupt:
        print()
        print("KeyboardInterrupt received")
        
    finally:
        stop_log_capture_threads(new_threads)
        shutdown_event.set()
        
        print("STOPPING COORDINATOR")
        driver.stop("whirlpool-server")
        
        print("WAITING FOR NEW BLOCK TO BE MINED")
        node.wait_for_new_block()
        
        print("COLLECTING COINS FROM WALLETS")
        for client in clients:
            if client.mnemonic is not None:
                print(f"Deriving address and sending bitcoin for {client.name}")
                manager.pathDerivation.send_all_tbtc_back(client.mnemonic)
    
        sleep(10)
        print("CLEANUP OF IMAGES")
        driver.cleanup(args.image_prefix)

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
        choices=["docker", "kubernetes"],
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
    parser.add_argument("--wif", type=str, default="")
    parser.add_argument("--wallet", type=str, default="")

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
