FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y openjdk-18-jdk-headless iptables tar curl iputils-ping && \
    rm -rf /var/lib/apt/lists/* \

WORKDIR /usr/src/app
COPY sparrow-1.7.10-x86_64.tar.gz .
RUN mkdir -p /root/.sparrow/testnet/wallets
COPY testnet4.mv.db /root/.sparrow/testnet/wallets/
COPY config /root/.sparrow/testnet
RUN tar -xzf sparrow-1.7.10-x86_64.tar.gz && \
    rm sparrow-1.7.10-x86_64.tar.gz
CMD ["/usr/src/app/Sparrow/bin/Sparrow", "-t", "--network", "testnet"]