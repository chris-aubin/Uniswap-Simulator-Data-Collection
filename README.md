# Uniswap-Simulator-Data-Collection

This repo contains the scripts that were used to collect the data necessary to backtest Uniswap v3 liquidity provision strategies using the [Uniswap v3 simulator](https://github.com/chris-aubin/Uniswap-Simulator) that I built as part of my senior (undergraduate) thesis in the Computer Science department at Princeton University. Because it has been my experience that completing even the most simple blockchain-related task tends to be far more complicated than it should be, I have focused on thoroughly documenting all of my code and explaining all of my decisions. I have erred on the side of including excess notes and observations in the hope of including anything that may be helpful to other developers. The keys/ URLs used to access APIs were deactivated as of making this repository public.

## collect_data_for_sim.py

## transactions.py
This module fetches all of a pools mint, burn, swap, flash and collect events. The events are printed as a JSON object. It uses the Etherscan API (https://docs.etherscan.io). Etherscan is the leading blockchain explorer, search, API and analytics platform for Ethereum. It also uses the PyCryptodome library (https://www.pycryptodome.org) for computing keccak hashes. It also uses the eth_abi package (https://eth-abi.readthedocs.io/en/latest/index.html) and the eth_utils packages(https://eth-utils.readthedocs.io/en/stable/) to decode events and compute the checksum (https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md) for addresses. Both packages are used internally by web3py.

This is an example of an event emitted by the WBT / ETH pool:

```
{
    "address": "0xcbcdf9626bc03e24f779434178a73a0b4bad62ed",
    "topics": [
        "0x98636036cb66a9c19a37435efc1e90142190214e8abeb821bdba3f2990dd4c95"
    ],
    "data": "0x0000000000000000000000000000000000061b1a1c878c3621dac27d63b440af000000000000000000000000000000000000000000000000000000000003efd5",
    "blockNumber": "0xbcbf9d",
    "blockHash": "0x6e6fa02e3efa1c3cb3aa3fa79e3a81e89e2bba0be10836c4893e8bee0fe06b6b",
    "timeStamp": "0x6091a9fe",
    "gasPrice": "0xba43b7400",
    "gasUsed": "0x50ce08",
    "logIndex": "0x25",
    "transactionHash": "0xf87d91f3d72a8e912c020c2e316151f3557b1217b44d4f6b6bec126448318530",
    "transactionIndex": "0x11"
}
```

- `address` is the address of the contract
- `topics` is an array containing the following:
- `topics[0]` is `keccak(EVENT_NAME + "(" + EVENT_ARGS.map(canonical_type_of).join(",") + ")")` 
    - `canonical_type_of` is a function that simply returns the canonical type of a given argument, e.g. for `uint256 indexed foo`, it would return `uint256`. 
    - If the event is declared as anonymous the topics[0] is not generated.
-`topics[n]` is `EVENT_INDEXED_ARGS[n - 1]` 
    - `EVENT_INDEXED_ARGS` is the series of `EVENT_ARGS` that are indexed
    - Up to 3 event arguments can be indexed. The indexed arguments are chosen by the engineer when the event is defined.
- `data`: `abi_serialise(EVENT_NON_INDEXED_ARGS)` 
    - `EVENT_NON_INDEXED_ARGS` is the series of `EVENT_ARGS` that are not indexed
    -  `abi_serialise` is the ABI serialisation function used for returning a series of typed values from a function, as per the specification [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#formal-specification-of-the-encoding)

Read more about Ethereum events [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#events) and read more about the formal encoding of Ethereum events [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#formal-specification-of-the-encoding).

#### Usage
To use the `transactions.py` script call:
```
python3 transactions.py pool_address start_date end_date
```

Where `pool_address` is the address of the pool for which you would like to fetch transactions, `start_date` is the the start of the date range (dd/mm/yyyy) for which you would like to fetch uniswap transactions and `end_date` is the the end of the date range (dd/mm/yyyy) for which you would like to fetch uniswap transactions . For example, the following would fetch all of the mints, burns, swaps, fetches and collects for the WBTC / ETH pool:

```
python3 transactions.py 0xcbcdf9626bc03e24f779434178a73a0b4bad62ed 31/03/2023 01/04/2023
```

## gas_estimates.py
Given a json object containing mints/burns/swaps/flashes/collects (typically those for a particular pool in a particular date range), calculates the average gas used to call each of those methods. The averages are printed as a JSON object. If a particular event doesn't occur, prints -1.

#### Usage
To use the `gas_estimates.py` simply call:
```
python3 gas_estimates.py path_to_transactions
```

Where `path_to_transactions` is the path to a file containing the output of `transactions.py`.


## relevant_positions.py
Given a json object containing mints/burns/swaps (typically those for a particular pool in a particular date range), prints a map from the `keccak256(abi.encodePacked(owner, tickLower, tickUpper))` to a string `owner+tickLower+tickUpper` for each position that was minted or burned. `keccak256(abi.encodePacked(owner, tickLower, tickUpper))` is used as the key for the position-indexed-state for a pool. Note, this prints the hex of `keccak256(abi.encodePacked(owner, tickLower, tickUpper))`, but the position-indexed state in a pool is a mapping from `bytes32 -> positions`.

#### Usage
To use the `relevant_positions.py` script call:
```
relevant\_positions.py path\_to\_transactions
```


## pool_state.py
This module uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a given date. The pool's state is printed as a json object the pool's slot0, fee growth global, protocol fees, liquidity and oracle observations. It contains part of the pool's tick-indexed state (specifically it contains 300 tick's worth of data on either side of the current tick at the specified block unless this value is overridden by the user). It contains part of the pools position-indexed state (specifically it contains the information for each of the positions specified in the positions list provided by the user - the idea being that the user can provide the list of positions that were changed (mint/burn) over the testing period so that those mints and burns can be simulated).

**N.B. This calls `balanceOf()` for `token0` and `token1` to determine the pool's balance of each token. Not all ERC20 tokens have a `balanceOf()` method (notably USDC does not have a `balanceOf()` method), and for pools containing those tokens this script will not work. It also will not work for ERC20 tokens that cannot be found on the list of Etherscan verified contracts, found [here](https://etherscan.io/contractsVerified).* 

#### Usage
To use the `pool_state.py` script call:
```
python3 pool_state.py pool_address date before path_to_positions surrounding_ticks
```

Where `pool_address` is the address of the relevant Uniswap v3 pool, `date` is the date at which to fetch the pool's state, `before` indicates whether  the state be fetched before or after the specified date (accepts 'before' or 'after'), `path_to_positions` is the path to a file containing a positions, `surrounding_ticks` is the number of ticks surrounding the current tick to fetch data for. For example, the following would fetch the pool state for the WBTC / ETH pool before 01/04/2023. It will only fetch the position-indexed-state for the positions in results/relevant_positions.txt and it will only fetch the tick indexed state for 300 ticks on with side of the active tick:

```
python3 pool_state.py 0xcbcdf9626bc03e24f779434178a73a0b4bad62ed 01/04/2023 before results/relevant_positions.txt 300 > results/pool_state_after.txt
```

## plot_liquidity.py
Plots the liquidity per tick for a given pool state (using output of pool_state.py).

#### Usage

## utils
