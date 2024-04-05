FROM ubuntu:latest as builder

RUN apt-get update && apt-get install -y \
    openjdk-18-jdk-headless \
    tar \
    git \
    rpm \
    fakeroot \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN git clone https://github.com/sparrowwallet/sparrow.git && \
    cd sparrow && \
    git submodule update --init --recursive

RUN sed -i 's/this.whirlpoolServer = WhirlpoolServer.valueOf(network.getName().toUpperCase(Locale.ROOT));/this.whirlpoolServer = WhirlpoolServer.LOCAL_TESTNET;/' /build/sparrow/src/main/java/com/sparrowwallet/sparrow/whirlpool/Whirlpool.java

RUN cd sparrow && \
    ./gradlew -Djava.awt.headless=true clean jpackage && \
    ./gradlew -Djava.awt.headless=true packageTarDistribution

FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    socat \
    tmux \
    tar \
    openjdk-18-jdk-headless \
    python3 \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -d /usr/src/app appuser

USER 1000:1000

WORKDIR /usr/src/app
COPY --from=builder /build/sparrow/build/jpackage/sparrow*.tar.gz .
RUN tar -xzf sparrow*.tar.gz && \
    rm sparrow*.tar.gz

COPY automation.py .
COPY utility.py .

RUN mkdir -p .sparrow/testnet/wallets
