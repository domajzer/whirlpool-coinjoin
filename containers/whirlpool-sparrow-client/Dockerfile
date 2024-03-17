FROM ubuntu:latest
#GOOD TO HAVE FOR DEBUG telnet curl
RUN apt-get update && \
    apt-get install -y openjdk-18-jdk-headless socat tar tmux python3 telnet iputils-ping curl iproute2 git rpm fakeroot && \
    rm -rf /var/lib/apt/lists/* 

WORKDIR /usr/src/app
COPY automation.py .
COPY utility.py .
COPY config /root/.sparrow/testnet

RUN git clone https://github.com/sparrowwallet/sparrow.git && \
    cd sparrow && \
    git submodule update --init --recursive

WORKDIR /usr/src/app/sparrow
RUN ./gradlew -Djava.awt.headless=true clean jpackage 
RUN ./gradlew -Djava.awt.headless=true packageTarDistribution

RUN cp /usr/src/app/sparrow/build/jpackage/sparrow*.tar.gz /usr/src/app/
WORKDIR /usr/src/app
RUN rm -rf sparrow/
RUN tar -xzf sparrow*.tar.gz && \
    rm sparrow*.tar.gz
