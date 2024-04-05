FROM ruimarinho/bitcoin-core:latest
EXPOSE 18332
COPY --chown=100:101 bitcoin.conf /home/bitcoin/.bitcoin/bitcoin.conf
USER 100:101
WORKDIR /home/bitcoin
ENTRYPOINT ["bitcoind", "-testnet", "-datadir=/home/bitcoin/.bitcoin"]
