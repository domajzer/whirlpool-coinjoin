FROM ubuntu:latest

RUN apt-get update && \
    apt-get install -y openjdk-18-jdk-headless socat tar tmux python3 telnet iputils-ping curl && \
    rm -rf /var/lib/apt/lists/* 

WORKDIR /usr/src/app
COPY sparrow-1.7.10-x86_64.tar.gz .
RUN mkdir -p /root/.sparrow/testnet/wallets

COPY testnet4.mv.db /root/.sparrow/testnet/wallets/
RUN  rm /root/.sparrow/testnet/wallets/testnet4.mv.db

COPY config /root/.sparrow/testnet

RUN tar -xzf sparrow-1.7.10-x86_64.tar.gz && \
    rm sparrow-1.7.10-x86_64.tar.gz

COPY automation.py .
COPY utility.py .

#CMD tmux new -d -s sparrow_session '/usr/src/app/Sparrow/bin/Sparrow --network testnet'; exec /bin/bash

#CMD ["/usr/src/app/Sparrow/bin/Sparrow", "-t", "--network", "testnet"]
