# Uniswap-Simulator-Data-Collection

This repo contains the scripts that were used to collect the data necessary to backtest Uniswap v3 liquidity provision strategies using the Uniswap v3 simulation that I built as part of my senior (undergraduate) thesis in the Computer Science department at Princeton University. Because it has been my experience that completing even the most simple blockchain-related task tends to be far more complicated than it should be, I have focused on thoroughly documenting all of my code and explaining all of my decisions. I have erred on the side of including excess notes and observations in the hope of including anything that may be helpful to other developers. The keys/ URLs used to access APIs were deactivated as of making this repository public.

## collect_data_for_sim.py

## transactions.py
This module fetches all of a pools mint, burn, swap, flash and collect events . It uses the Etherscan API (https://docs.etherscan.io). Etherscan is the leading blockchain explorer, search, API and analytics platform for Ethereum. It also uses the PyCryptodome library (https://www.pycryptodome.org) for computing keccak hashes. It also uses the eth_abi package (https://eth-abi.readthedocs.io/en/latest/index.html) and the eth_utils packages(https://eth-utils.readthedocs.io/en/stable/) to decode events and compute the checksum (https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md) for addresses. Both packages are used internally by web3py.

Events are emitted as part of the Ethereum logging/ event-watching protocol. Log entries from emitted events provide information about the function that emitted the event. Events contain the following information:
  - `address` is the address of the contract
  - `topics` is an array containing the following:
    - `topics[0]` is `keccak(EVENT_NAME + "(" + EVENT_ARGS.map(canonical_type_of).join(",") + ")")` 
      - `canonical_type_of` is a function that simply returns the canonical type of a given argument, e.g. for uint indexed foo, it would return uint256). 
      - If the event is declared as anonymous the topics[0] is not generated.
    - `topics[n]` is `EVENT_INDEXED_ARGS[n - 1]` 
      - `EVENT_INDEXED_ARGS` is the series of `EVENT_ARGS` that are indexed
      - Up to 3 event arguments can be indexed. The indexed arguments are chosen by the engineer when the event is defined.
  - `data`: `abi_serialise(EVENT_NON_INDEXED_ARGS)` 
    - `EVENT_NON_INDEXED_ARGS` is the series of `EVENT_ARGS` that are not indexed
    -  `abi_serialise` is the ABI serialisation function used for returning a series of typed values from a function, as per the specification [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#formal-specification-of-the-encoding)



Read more about Ethereum events [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#events) and read more about the formal encoding of Ethereum events [here](https://docs.soliditylang.org/en/v0.8.17/abi-spec.html#formal-specification-of-the-encoding).

#### Usage

## gas_estimates.py
Given a json object containing mints/burns/swaps/flashes/ (typically those for a particular pool in a particular date range), prints the average gas used to call each of those methods. If a particular event doesn't occur, prints -1.

#### Usage

## relevant_positions.py
Given a json object containing mints/burns/swaps (typically those for a particular pool in a particular date range), prints a map from the keccak256(abi.encodePacked(owner, tickLower, tickUpper)) to a string owner+tickLower+tickUpper for each position that was minted or burned. keccak256(abi.encodePacked(owner, tickLower, tickUpper)) is used as the key for the position-indexed-state for a pool. Note, this prints the hex of keccak256(abi.encodePacked(owner, tickLower, tickUpper)), but the position-indexed state in a pool is a mapping from bytes32 -> positions.

#### Usage

## pool_state.py
Uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a given date. The pool's state is returned as a dictionary containing the pool's slot0, fee growth global, protocol fees, liquidity and oracle observations. It contains part of the pool's tick-indexed state (specifically it contains 300 tick's worth of data on either side of the current tick at the specified block unless this value is overridden by the user). It contains part of the pools position-indexed state (specifically it contains the information for each of the positions specified in the positions list provided by the user - the idea being that the user can provide the list of positions that were changed (mint/burn) over the testing period so that those mints and burns can be simulated).

**N.B. This calls `balanceOf()` for `token0` and `token1` to determine the pool's balance of each token. Not all ERC20 tokens have a `balanceOf()` method (notably USDC does not have a `balanceOf()` method), and for pools containing those tokens this script will not work. It also will not work for ERC20 tokens that cannot be found on the list of Etherscan verified contracts, found [here](https://etherscan.io/contractsVerified).* 

#### Usage

## plot_liquidity.py
Plots the liquidity per tick for a given pool state (using output of pool_state.py).

#### Usage

## utils
