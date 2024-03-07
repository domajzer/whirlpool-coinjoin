from functools import cached_property
from io import BytesIO
import os
import tarfile
from . import Driver
import docker


class DockerDriver(Driver):
    def __init__(self, namespace="coinjoin"):
        self.client = docker.from_env()
        self._namespace = namespace

    @cached_property
    def network(self):
        networks = self.client.networks.list(names=[self._namespace])
        if networks:
            print(f"Using existing network: {self._namespace}")
            return networks[0]
        else:
            print(f"Creating new network: {self._namespace}")
            return self.client.networks.create(self._namespace, driver="bridge")

    def has_image(self, name):
        try:
            self.client.images.get(name)
            return True
        except docker.errors.ImageNotFound:
            return False

    def build(self, name, path):
        self.client.images.build(path=path, tag=name, rm=True, nocache=True)

    def pull(self, name):
        self.client.images.pull(name)

    def run(
        self,
        name,
        image,
        env=None,
        ports=None,
        skip_ip=False,
        cpu=0.6,
        memory=800,
        volumes=None,
        tty=False,
        command=None
    ):
        self.client.containers.run(
            image,
            detach=True,
            auto_remove=False,
            name=name,
            hostname=name,
            network=self.network.id,
            ports=ports or {},
            environment=env or {},
            volumes=volumes or {},
            tty=tty,
            command=command
        )
        return "", ports

    def stop(self, name):
        try:
            self.client.containers.get(name).stop()
            print(f"- stopped {name}")
        except docker.errors.NotFound:
            pass

    def download(self, name, src_path, dst_path):
        try:
            stream, _ = self.client.containers.get(name).get_archive(src_path)

            fo = BytesIO()
            for d in stream:
                fo.write(d)
            fo.seek(0)
            with tarfile.open(fileobj=fo) as tar:
                tar.extractall(dst_path)
        except:
            pass

    def peek(self, name, path):
        stream, _ = self.client.containers.get(name).get_archive(path)

        fo = BytesIO()
        for d in stream:
            fo.write(d)
        fo.seek(0)
        with tarfile.open(fileobj=fo) as tar:
            return tar.extractfile(os.path.basename(path)).read().decode()

    def upload(self, name, src_path, dst_path):
        fo = BytesIO()
        with tarfile.open(fileobj=fo, mode="w") as tar:
            tar.add(src_path, os.path.basename(dst_path))
        fo.seek(0)
        self.client.containers.get(name).put_archive(os.path.dirname(dst_path), fo)

    def setup_socat_in_container(self, container_name, coordinator_ip):
        container = self.client.containers.get(container_name)
        cmd = f"socat TCP-LISTEN:8080,fork TCP:{coordinator_ip}:8080"
        try:
            container.exec_run(cmd, detach=True)
            print(f"Started socat in {container_name}.")
            
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
    
    def get_container_ip(self, name):
        container = self.client.containers.get(name)
        container.reload()
        ip_address = container.attrs['NetworkSettings']['Networks'][self.network.name]['IPAddress']
        return ip_address

    def capture_and_save_logs(self, client, log_file_path):
        try:
            container = self.client.containers.get(client.name)
            logs = container.logs().decode("utf-8")
            
            with open(log_file_path, "w") as log_file:
                log_file.write(logs)
            print(f"Captured and saved logs for {client.name} to {log_file_path}")
        except Exception as e:
            print(f"Failed to capture and save logs for {client.name}: {e}")
    
    def cleanup(self, image_prefix=""):
        containers = list(
            filter(
                lambda x: x.attrs["Config"]["Image"]
                in (
                    f"{image_prefix}bitcoin-testnet-node",
                    f"{image_prefix}whirlpool-db",
                    f"{image_prefix}whirlpool-server",
                    f"{image_prefix}whirlpool-sparrow-client",                    
                ),
                self.client.containers.list(),
            )
        )
        self.stop_many(map(lambda x: x.name, containers))
        networks = self.client.networks.list(self._namespace)
        if networks:
            for network in networks:
                network.remove() 
