import docker
import os
import re
import time
import subprocess
import threading
import walletmanager

# Constants
PROVISION_NUMBER_FIRST_LIQUIDITY = [i for i in range(1,4)]
PROVISION_NUMBER_AFTER_LIQUIDITY = [i for i in range(1,3)]
NETWORK_NAME = "whirlpool-net"
MYSQL_IMAGE_TAG = "whirlpool-db"
PYTHON_IMAGE_TAG = "whirlpool-db-init"
WHIRLPOOL_SERVER_IMAGE_TAG = "whirlpool-server"
MYSQL_CONTAINER_NAME = "whirlpool-db"
PYTHON_CONTAINER_NAME = "whirlpool-db-init"
WHIRLPOOL_SERVER_CONTAINER_NAME = "whirlpool-server"
BITCOIN_IMAGE_TAG = "bitcoin-testnet-node"
BITCOIN_CONTAINER_NAME = "bitcoin-testnet-node"
SPARROW_IMAGE_TAG = "whirlpool-sparrow"
WALLETS_PATH = "whirlpool-sparrow-client/wallets"
MYSQL_VOLUME_NAME = "whirlpool-mysql-data"
premix_check = 0

#INIT
available_wallets = os.listdir(WALLETS_PATH)
used_wallets = set()
docker_client = docker.from_env()
shutdown_event = threading.Event()

try:
    network = docker_client.networks.get(NETWORK_NAME)
    print(f"Using existing network: {NETWORK_NAME}")
except docker.errors.NotFound:
    network = docker_client.networks.create(NETWORK_NAME, driver="bridge")
    print(f"Created network: {NETWORK_NAME}")

def build_and_run_mysql_container():
    print("Building MySQL Docker image for Whirlpool DB")
    docker_client.images.build(
        path="./coordinator-docker", dockerfile='Dockerfile.whirlpool-db', tag=MYSQL_IMAGE_TAG, rm=True
    )
    print("- MySQL image built")
    
    try:
        mysql_container = docker_client.containers.get(MYSQL_CONTAINER_NAME)
        if mysql_container.status == 'running':
            print(f"Container '{MYSQL_CONTAINER_NAME}' is already running.")
            return mysql_container
        elif mysql_container.status == 'exited':
            print(f"Container '{MYSQL_CONTAINER_NAME}' has exited. Removing and starting a new one.")
            mysql_container.remove()
        else:
            print(f"Container '{MYSQL_CONTAINER_NAME}' is in an unexpected state: {mysql_container.status}.")
            return mysql_container
    except docker.errors.NotFound:
        print(f"Container '{MYSQL_CONTAINER_NAME}' not found. Will create a new one.")

    print(f"Starting container '{MYSQL_CONTAINER_NAME}'")
    mysql_container = docker_client.containers.run(
        MYSQL_IMAGE_TAG,
        detach=True,
        name=MYSQL_CONTAINER_NAME,
        environment={'MYSQL_ROOT_PASSWORD': 'root', 'MYSQL_DATABASE': 'whirlpool_testnet'},
        ports={'3306/tcp': 3307},
        network=NETWORK_NAME,
        remove=True,
        volumes={MYSQL_VOLUME_NAME: {'bind': '/var/lib/mysql', 'mode': 'rw'}}
    )
    
    print(f"Container '{MYSQL_CONTAINER_NAME}' started")
    time.sleep(10) 
    return mysql_container

def build_and_run_python_container():
    print("Building Python Docker image for DB initialization")
    docker_client.images.build(
        path="./coordinator-docker", dockerfile='Dockerfile.db', tag=PYTHON_IMAGE_TAG, rm=True
    )
    print("- Python image built")
    
    print(f"Starting container '{PYTHON_CONTAINER_NAME}'")
    python_container = docker_client.containers.run(
        PYTHON_IMAGE_TAG,
        detach=True,
        name=PYTHON_CONTAINER_NAME,
        environment={'MYSQL_ROOT_PASSWORD': 'root'},
        network=NETWORK_NAME,
        remove=True
    )
    print(f"Container '{PYTHON_CONTAINER_NAME}' started")
    time.sleep(5) 
    return python_container

def build_whirlpool_server():
    print("Building Docker image for Whirlpool Server")
    try:
        docker_client.images.build(
            path="./coordinator-docker", dockerfile='Dockerfile.whirlpool', tag=WHIRLPOOL_SERVER_IMAGE_TAG, rm=True
        )
        print("- Whirlpool Server image built successfully")
    except Exception as e:
        print(f"Failed to build Whirlpool Server image: {e}")
    
def run_whirlpool_server_container():
    try:
        whirlpool_server_container = docker_client.containers.get(WHIRLPOOL_SERVER_CONTAINER_NAME)
        if whirlpool_server_container.status == 'running':
            print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' is already running.")
            return whirlpool_server_container
        elif whirlpool_server_container.status == 'exited':
            print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' has exited. Removing and starting a new one.")
            whirlpool_server_container.remove()
        else:
            print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' is in an unexpected state: {whirlpool_server_container.status}.")
            return whirlpool_server_container
    except docker.errors.NotFound:
        print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' not found. Creating a new one.")
    
    print(f"Starting container '{WHIRLPOOL_SERVER_CONTAINER_NAME}'")
    whirlpool_server_container = docker_client.containers.run(
        WHIRLPOOL_SERVER_IMAGE_TAG,
        detach=True,
        name=WHIRLPOOL_SERVER_CONTAINER_NAME,
        ports={'8080/tcp': 8080},
        network='bridge',
        remove=False
    )
    print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' started")
    default_bridge_network = docker_client.networks.get('bridge')
    default_bridge_network.disconnect(whirlpool_server_container)
    
    FIXED_IP = "172.18.0.10"
    network.connect(whirlpool_server_container, ipv4_address=FIXED_IP)
     
    print(f"Container '{WHIRLPOOL_SERVER_CONTAINER_NAME}' started with IP: {FIXED_IP}")
    time.sleep(10)
    return whirlpool_server_container

def build_and_run_bitcoin_container():
    print("Checking for Bitcoin Testnet Node Docker image")
    image_tag = BITCOIN_IMAGE_TAG

    existing_images = docker_client.images.list(name=image_tag)
    if not existing_images: 
        print(f"Image '{image_tag}' does not exist. Building new image.")
        btc_docker_path = "./btc-docker"
        image, build_logs = docker_client.images.build(
            path=btc_docker_path, tag=image_tag, rm=True
        )
        for chunk in build_logs:
            if 'stream' in chunk:
                print(chunk['stream'].strip())
        print("Docker image built successfully")
    else:
        print(f"Image '{image_tag}' already exists. Skipping build.")

    print(f"Starting container '{BITCOIN_CONTAINER_NAME}'")
    testnet3_path = os.path.abspath("./btc-docker/testnet3")
    try:
        container = docker_client.containers.get(BITCOIN_CONTAINER_NAME)
        if container.status == 'running':
            print(f"Container '{BITCOIN_CONTAINER_NAME}' is already running.")
            return container
        elif container.status == 'exited':
            print(f"Container '{BITCOIN_CONTAINER_NAME}' has exited. Removing and starting a new one.")
            container.remove()
        else:
            print(f"Container '{BITCOIN_CONTAINER_NAME}' is in an unexpected state: {container.status}.")
            return container
    except docker.errors.NotFound:
        print(f"Container '{BITCOIN_CONTAINER_NAME}' not found. Will create a new one.")
    
    container = docker_client.containers.run(
        image_tag,
        detach=True,
        name=BITCOIN_CONTAINER_NAME,
        ports={'18332/tcp': 18332},
        volumes={testnet3_path: {'bind': '/home/bitcoin/.bitcoin/testnet3', 'mode': 'rw'}},
        network=NETWORK_NAME,
        remove=True
    )
    print(f"Container '{BITCOIN_CONTAINER_NAME}' started")
    time.sleep(20)
    return container

def build_sparrow_container():
    print("Building Docker image for Whirlpool Sparrow Client")
    docker_client.images.build(
        path="./whirlpool-sparrow-client", tag=SPARROW_IMAGE_TAG, rm=True
    )

def run_sparrow_container(sparrow_container_name):
    cmd = f"python3 /usr/src/app/automation.py -debug -mix -create -name {sparrow_container_name}"
    print(f"Starting container '{sparrow_container_name}'")
    sparrow_container = docker_client.containers.run(
        SPARROW_IMAGE_TAG,
        detach=True,
        name=sparrow_container_name,
        network=NETWORK_NAME,
        remove=False,
        tty=True,
        privileged=True,
        command=cmd
    )
    print(f"Container '{sparrow_container_name}' started")
    return sparrow_container

def get_container_ip(container_name):
    container = docker_client.containers.get(container_name)
    return container.attrs['NetworkSettings']['Networks'][NETWORK_NAME]['IPAddress']

def setup_socat_in_container(container_name, maven_ip):
    container = docker_client.containers.get(container_name)
    cmd = f"socat TCP-LISTEN:8080,fork TCP:{maven_ip}:8080"
    try:
        container.exec_run(cmd, detach=True)
        print(f"Started socat in {container_name}.")

        time.sleep(3)
        
        result = container.exec_run(["/bin/sh", "-c", "ps aux | grep socat"])
        if "TCP-LISTEN" in result.output.decode():
            print(f"Socat is running in {container_name}.")
        else:
            print(f"Failed to start socat in {container_name}.")
            return False
        return True
    except Exception as e:
        print(f"Exception setting up socat in container {container_name}: {e}")
        return False

def copy_wallet_to_container(container_name, wallet_file):
    wallet_file_path = os.path.join(WALLETS_PATH, wallet_file)
    destination_path = f"{container_name}:/root/.sparrow/testnet/wallets/"
    
    try:
        subprocess.run(["docker", "cp", wallet_file_path, destination_path], check=True)
        print(f"Copied {wallet_file} to container {container_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy {wallet_file} to container {container_name}: {e}")

def copy_file_from_container(container_name, file_path_in_container, host_destination_path):
    try:
        subprocess.run(["docker", "cp", f"{container_name}:{file_path_in_container}", host_destination_path], check=True)
        print(f"Copied {file_path_in_container} from {container_name} to {host_destination_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy file from {container_name}: {e}")

def build_logs_file(container_name):
    try:
        with open(f"whirlpool-sparrow-client/logs/{container_name}.txt", "w") as file:
            subprocess.run(["docker", "logs", container_name], stdout=file, check=True)
        print(f"Created a logfile of {container_name}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create a logfile of {container_name}: {e}")

def parse_address_send_btc(log_file_path):
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
                    
                    if tbtc_address not in addresses_in_file:
                        with open(output_file_path, 'a') as file2:
                            file2.write(tbtc_address + '\n')
                            addresses_in_file.add(tbtc_address)
                if re.search(premix_UTXO_mixed_pattern, line):
                    pattern_found = True
                      
    except FileNotFoundError:
        print(f"Log file {log_file_path} not found")
    
    return pattern_found

def send_btc(input_path, output_path, amount, btc_node):
    try:
        with open(output_path, 'r+') as output_file:
            sent_addresses = set(output_file.read().splitlines())
        
        #wallet_info = btc_node.get_wallet_info()
        #print("Wallet Info:", wallet_info)
        
        with open(input_path, 'r+') as input_file, open(output_path, 'a+') as output_file:
            for address in input_file:
                address = address.strip()
                if address and address not in sent_addresses:
                    try:
                        transaction_info = btc_node.fund_address(address, amount)
                        print("Transaction info:", transaction_info)
                        output_file.write(address + '\n')
                        
                    except Exception as e:
                        print(f"Error sending BTC to {address}: {e}")
                        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        
    except Exception as e:
        print(f"Error in send_btc: {e}")

def capture_logs_periodically(container_names, amount, btc_node, premix_matched_containers, interval=55):
    global premix_check
    if shutdown_event.is_set():
        return
    
    for container_name in container_names:
        time.sleep(2)
        build_logs_file(container_name)
        if parse_address_send_btc(f"whirlpool-sparrow-client/logs/{container_name}.txt") and (premix_check == 0):
            premix_matched_containers.add(container_name)
            print(f"Container {container_name} has finished mixing premix UTXO.")
            
    if (premix_matched_containers == set(container_names)) and (premix_check == 0):
        subprocess.run(['docker', 'cp', 'stopfile', f'{WHIRLPOOL_SERVER_CONTAINER_NAME}:/app/stopfile'], check=True)
        premix_check = 1

    send_btc("whirlpool-sparrow-client/tmp/addresses.txt","whirlpool-sparrow-client/tmp/addresses_send.txt", amount, btc_node)
    
    if not shutdown_event.is_set():
        timer = threading.Timer(interval, capture_logs_periodically, [container_names, amount, btc_node, premix_matched_containers,interval])
        timer.start()
        
def main(): 
    btc_node = walletmanager.BtcNode(
        host="localhost",
        port=18332,
        rpc_user="TestnetUser1",
        rpc_password="Testnet123"
    )
    premix_matched_containers = set()
    build_and_run_bitcoin_container()
    build_and_run_mysql_container()
    #time.sleep(120)
    print("Waiting for MySQL container to initialize...")
    build_and_run_python_container()
    build_whirlpool_server()
    run_whirlpool_server_container()
    #time.sleep(10)
    maven_ip = get_container_ip(WHIRLPOOL_SERVER_CONTAINER_NAME)
    #time.sleep(30)
    
    build_sparrow_container()
    time.sleep(20)

    wallet_containers = []
    default_containers = [BITCOIN_CONTAINER_NAME, MYSQL_CONTAINER_NAME, WHIRLPOOL_SERVER_CONTAINER_NAME]
    for wallet in PROVISION_NUMBER_FIRST_LIQUIDITY:
        sparrow_container_name = f"{SPARROW_IMAGE_TAG}-liquidity-{wallet}"
        
        run_sparrow_container(sparrow_container_name)
        setup_socat_in_container(sparrow_container_name, maven_ip)
        
        for wallet_file in available_wallets:
            if wallet_file not in used_wallets:
                print(f"Copying '{wallet_file} into '{sparrow_container_name}'")
                copy_wallet_to_container(sparrow_container_name, wallet_file)
                used_wallets.add(wallet_file)
                break
        
        wallet_containers.append(sparrow_container_name)
        time.sleep(30)
        
    capture_logs_periodically(wallet_containers, 0.0002, btc_node, premix_matched_containers)
    while(premix_check == 0):
        time.sleep(30)
    
    for wallet in PROVISION_NUMBER_AFTER_LIQUIDITY:
        sparrow_container_name = f"{SPARROW_IMAGE_TAG}-{wallet}"
        
        run_sparrow_container(sparrow_container_name)
        setup_socat_in_container(sparrow_container_name, maven_ip)
        
        for wallet_file in available_wallets:
            if wallet_file not in used_wallets:
                print(f"Copying '{wallet_file} into '{sparrow_container_name}'")
                copy_wallet_to_container(sparrow_container_name, wallet_file)
                used_wallets.add(wallet_file)
                break
        
        wallet_containers.append(sparrow_container_name)
        time.sleep(30)
    
    
    input("Press Enter to stop all running sparrow containers...\n")
    
    shutdown_event.set()
    maven_export_dir = "/app/logs"
    mixs_file_path = f"{maven_export_dir}/mixs.csv"
    activity_file_path = f"{maven_export_dir}/activity.csv"
    
    for container_name in wallet_containers:
        print(f"Stopping wallet container '{container_name}'")
        container = docker_client.containers.get(container_name)
        container.stop()
        print(f"Wallet container '{container_name}' stopped")
    
    input("Press Enter to stop all other running containers...\n")
    
    for container_name in default_containers:
        print(f"Stopping container '{container_name}'")
        
        if container_name == WHIRLPOOL_SERVER_CONTAINER_NAME:
            copy_file_from_container(WHIRLPOOL_SERVER_CONTAINER_NAME, mixs_file_path, "coordinator-docker/logs")
            copy_file_from_container(WHIRLPOOL_SERVER_CONTAINER_NAME, activity_file_path, "coordinator-docker/logs")

        container = docker_client.containers.get(container_name)
        container.stop()
        print(f"Container '{container_name}' stopped")

if __name__ == "__main__":
    main()
    
