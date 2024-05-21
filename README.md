# CoinJoin simulation setup

A container-based setup for simulating CoinJoins on Testnet network.

## Usage

1. Install [Docker](https://docker.com/) and [Python](http://python.org/).
2. Clone the repository `git clone https://github.com/domajzer/whirlpool-coinjoin.git`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run the default scenario with the default driver: `python manager.py run`.
   - [Scenario](#scenarios) definition file can be specified using the `--scenario` option.
5. For running the analysis script you need to download and install 'https://github.com/Samourai-Wallet/boltzmann'

## Scenarios

Scenario definition files can be passed to the simulation script using the `--scenario` option. The scenario definition is a JSON file with the following structure:

```json
{
    "name": "50-wallets-2utxo",
    "rounds": 10,
    "blocks": 0,
    "liquidity-wallets": [
      {"funds": [50000], "delay": 0},
      {"funds": [50000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0}
    ],
    "wallets": [
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      {"funds": [35000], "delay": 0},
      .....
    ]
}
```

The fields are as follows:
- `name` field is the name of the scenario used for output logs.
- `blocks` field is the number of mined blocks after which the simulation terminates. If set to 0, the simulation will run indefinitely.
- `wallets` field is a list of wallet configurations. Each wallet configuration is a dictionary with the following fields:
  - `funds` is a list of funds in satoshis that the wallet will use for coinjoins.
  - `delay` is the number of blocks the wallet will wait before joining coinjoins.

## Advanced usage

The simulation script enables advanced configuration for running on different container platforms with various networking setups. This section describes the advanced configuration and shows common examples.

### Backend driver


#### Docker

The default driver is `docker`. Running `docker` requires [Docker](https://www.docker.com/) installed locally and running.

#### Kubernetes

To run the simulation on a [Kubernetes](https://kubernetes.io/) cluster, use the `kubernetes` driver. The driver requires a running Kubernetes cluster and `kubectl` configured to access the cluster. 

The `kubernetes` driver relies on used images being accessible publicly from [DockerHub](https://hub.docker.com/). For that, build the images in `containers` directory manually and upload them to the registry. Afterwards, specify the image prefix using `--image-prefix` option when starting the simulation.

In case *NodePorts* are not supported by your cluster, you may also need to run a proxy to access the services, e.g., [Shadowsocks](https://shadowsocks.org/). Use the `--proxy` option to specify the address of the proxy.

If you need to specify custom namespace, use the `--namespace` option. If you also need to reuse existing namespace, use the `--reuse-namespace` option.

##### Example

Running the simulation on a remote cluster using pre-existing namespace and a wallet import:
```bash
python manager1.py run --driver kubernetes --namespace custom-coinjoin --wallet containers/bitcoin-testnet-node/wallets/wallet --reuse-namespace --image-prefix "domajzer99/" --scenario "scenario50.json"
```
