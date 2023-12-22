FROM ruimarinho/bitcoin-core:latest
COPY bitcoin.conf /home/bitcoin/.bitcoin/bitcoin.conf
EXPOSE 18332
CMD ["bitcoind", "-testnet"]

