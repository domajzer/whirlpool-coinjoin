import docker
import os
import time
import subprocess

# Constants
NETWORK_NAME = "whirlpool-net"
MYSQL_IMAGE_TAG = "whirlpool-db"
PYTHON_IMAGE_TAG = "whirlpool-db-init"
MAVEN_IMAGE_TAG = "whirlpool-server"
MYSQL_CONTAINER_NAME = "whirlpool-db"
PYTHON_CONTAINER_NAME = "whirlpool-db-init"
MAVEN_CONTAINER_NAME = "whirlpool-server"
BITCOIN_IMAGE_TAG = "bitcoin-testnet-node"
BITCOIN_CONTAINER_NAME = "bitcoin-testnet-node"
SPARROW_IMAGE_TAG = "whirlpool-sparrow"
SPARROW_CONTAINER_NAME = "whirlpool-sparrow"

docker_client = docker.from_env()

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
        remove=True
    )
    print(f"Container '{MYSQL_CONTAINER_NAME}' started")
    time.sleep(30) 
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
    time.sleep(15) 
    return python_container

def build_and_run_maven_container():
    print("Building Maven Docker image for Whirlpool Server")
    docker_client.images.build(
        path="./coordinator-docker", dockerfile='Dockerfile.whirlpool', tag=MAVEN_IMAGE_TAG, rm=True
    )
    print("- Maven image built")
    try:
        maven_container = docker_client.containers.get(MAVEN_CONTAINER_NAME)
        if maven_container.status == 'running':
            print(f"Container '{MAVEN_CONTAINER_NAME}' is already running.")
            return maven_container
        elif maven_container.status == 'exited':
            print(f"Container '{MAVEN_CONTAINER_NAME}' has exited. Removing and starting a new one.")
            maven_container.remove()
        else:
            print(f"Container '{MAVEN_CONTAINER_NAME}' is in an unexpected state: {maven_container.status}.")
            return maven_container
    except docker.errors.NotFound:
        print(f"Container '{MAVEN_CONTAINER_NAME}' not found. Will create a new one.")

    print(f"Starting container '{MAVEN_CONTAINER_NAME}'")
    maven_container = docker_client.containers.run(
        MAVEN_IMAGE_TAG,
        detach=True,
        name=MAVEN_CONTAINER_NAME,
        ports={'8081/tcp': 8081},
        network='bridge',
        remove=True
    )
    print(f"Container '{MAVEN_CONTAINER_NAME}' started")
    default_bridge_network = docker_client.networks.get('bridge')
    default_bridge_network.disconnect(maven_container)
    
    FIXED_IP = "172.18.0.10"
    network.connect(maven_container, ipv4_address=FIXED_IP)
    
    print(f"Container '{MAVEN_CONTAINER_NAME}' started with IP: {FIXED_IP}")
    time.sleep(20)
    return maven_container

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
    return container

def build_and_run_sparrow_container(maven_ip):
    print("Building Docker image for Whirlpool Sparrow Client")
    docker_client.images.build(
        path="./whirlpool-sparrow-client", tag=SPARROW_IMAGE_TAG, rm=True
    )
    print("- Sparrow image built")
    
    print(f"Starting container '{SPARROW_CONTAINER_NAME}'")
    sparrow_container = docker_client.containers.run(
        SPARROW_IMAGE_TAG,
        detach=True,
        name=SPARROW_CONTAINER_NAME,
        network=NETWORK_NAME,
        environment={'MAVEN_SERVICE_ADDRESS': f"{maven_ip}:8081"},
        remove=True,
        tty=True,
        privileged=True
    )
    
    print(f"Container '{SPARROW_CONTAINER_NAME}' started")
    return sparrow_container

def get_container_ip(container_name):
    container = docker_client.containers.get(container_name)
    return container.attrs['NetworkSettings']['Networks'][NETWORK_NAME]['IPAddress']

def main():
    bitcoin_container = build_and_run_bitcoin_container()
    mysql_container = build_and_run_mysql_container()
    
    print("Waiting for MySQL container to initialize...")
    python_container = build_and_run_python_container()
        
    maven_container = build_and_run_maven_container()
    maven_ip = get_container_ip(MAVEN_CONTAINER_NAME)
    time.sleep(5)
    sparrow_wallet = build_and_run_sparrow_container(maven_ip)
    time.sleep(5)
    input("Press Enter to stop all running containers...\n")
        
    for container in [bitcoin_container, mysql_container, python_container, maven_container,sparrow_wallet]:
        print(f"Stopping container '{container.name}'")
        container.stop()
        print(f"Container '{container.name}' stopped")

if __name__ == "__main__":
    main()