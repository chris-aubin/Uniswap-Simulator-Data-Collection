""" Fetches a pool's state at a given block.

    Uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a given
    block. The pool's state is returned as a dictionary containing the pool's
    slot0, fee growth global, protocol fees, liquidity and oracle observations.
    It contains part of the pool's tick-indexed state (specifically it contains 
    300 tick's worth of data on either side of the current tick at the 
    specified block unless this value is overridden by the user). It contains
    part of the pools position-indexed state (specifically it contains the
    information for each of the positions specified in the positions list
    provided by the user - the idea being that the user can provide the list of 
    positions that were changed (mint/burn) over the testing period so that 
    those mints and burns can be simulated).
"""


#-----------------------------------------------------------------------
# pool_state.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import json
import math
import sys

from web3 import Web3
from utils.uniswap_pool_abi import UNISWAP_POOL_ABI


#-----------------------------------------------------------------------


DEFAULT_SURROUNDING_TICKS = 300
INFURA_PROVIDER           = "https://mainnet.infura.io/v3/0c7d3f029eb34415866f7e943521f4ee"


def get_pool_state(
        pool_address,
        positions,
        block,
        surrounding_ticks = DEFAULT_SURROUNDING_TICKS,
        ):
    """ Fetches a pool's state at a given block.
    
        Uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a 
        given block. The pool's state is returned as a dictionary containing 
        the pool's slot0, fee growth global, protocol fees, liquidity and 
        oracle observations. It contains part of the pool's tick-indexed state 
        (specifically it contains 300 tick's worth of data on either side of 
        the current tick at the specified block unless this value is overridden
        by the user). It contains part of the pools position-indexed state 
        (specifically it contains the information for each of the positions 
        specified in the positions list provided by the user - the idea being 
        that the user can provide the list of positions that were changed 
        (mint/burn) over the testing period so that those mints and burns can 
        be simulated).

        Keyword arguments:
        pool_address      -- the address of the pool
        positions         -- a list of positions that were changed over the
                             testing period
        block             -- the block at which to fetch the pool's state
        surrounding_ticks -- the number of ticks on either side of the current
                             tick to fetch data for (default 300)
    """

    # Initialize web3 and the pool contract
    w3   = Web3(Web3.HTTPProvider(INFURA_PROVIDER))
    pool = w3.eth.contract(address=Web3.to_checksum_address(pool_address), abi=UNISWAP_POOL_ABI)

    # Fetch the pool's state by calling the getters that solidity generates
    # automatically for each public state variable.
    fee_growth_global0X128 = pool.functions.feeGrowthGlobal0X128().call()
    fee_growth_global1X128 = pool.functions.feeGrowthGlobal1X128().call()
    protocol_fees          = pool.functions.protocolFees().call()
    liquidity              = pool.functions.liquidity().call()
    slot0                  = pool.functions.slot0().call()
    tick_spacing           = pool.functions.tickSpacing().call()

    pool_state = {
        "tickSpacing":          tick_spacing,
        "feeGrowthGlobal0X128": fee_growth_global0X128,
        "feeGrowthGlobal1X128": fee_growth_global1X128,
        "protocolFees":         protocol_fees,
        "liquidity":            liquidity,
        "slot0":                {"sqrtPriceX96": slot0[0], "tick": slot0[1], "observationIndex": slot0[2], "observationCardinality": slot0[3], "feeProtocol": slot0[4]}
    }

    current_tick_idx = pool_state["slot0"]["tick"]
    tick_spacing     = pool_state["tickSpacing"]

    # The pools current tick isn't necessarily a tick that can actually be initialized.
    # Only ticks that are divisible by tick_spacing can be initialized. So we need to
    # find the nearest initializable tick using the tick spacing.
    active_tick_idx = math.floor(current_tick_idx / tick_spacing) * tick_spacing
        if active_tick_idx < MIN_TICK:
            active_tick_idx = MIN_TICK
        elif active_tick_idx > MAX_TICK: 
            active_tick_idx = MAX_TICK
    
    # Fetch the array of oracle observations (observationCardinality is the 
    # max number of observations the observations array is currently configured
    # to store)
    observations = []
    for i in range(pool_state["slot0"]["observationCardinality"]):
        observations.append(pool.functions.observations(i).call())
    pool_state["observations"] = observations

    # Fetch the tick information for the specified number of ticks above 
    # and below the current tick. 
    tick_indexed_state = {}
    tick = active_tick_idx
    for i in range(1, DEFAULT_SURROUNDING_TICKS):
        tick                     += i*tick_spacing
        tick_indexed_state[tick] = pool.functions.ticks(tick).call()
    tick = active_tick_idx
    for i in range(1, DEFAULT_SURROUNDING_TICKS):
        tick                     -= i*tick_spacing
        tick_indexed_state[tick] = pool.functions.ticks(tick).call()
    pool_state["ticks"] = tick_indexed_state

    # Fetch the position information for the positions specified by the user
    position_indexed_state = {}
    for position_key in position_addresses:
        position = pool.functions.positions(position_key).call()
        position_indexed_state[position_key] = position
    pool_state["positions"] = position_indexed_state

    return pool_state
    


def parse_args():
    """Parses the command-line arguments."""

    description = """Uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a 
        given block. The pool's state is returned as a dictionary containing 
        the pool's slot0, fee growth global, protocol fees, liquidity and 
        oracle observations. It contains part of the pool's tick-indexed state 
        (specifically it contains 300 tick's worth of data on either side of 
        the current tick at the specified block unless this value is overridden
        by the user). It contains part of the pools position-indexed state 
        (specifically it contains the information for each of the positions 
        specified in the positions list provided by the user - the idea being 
        that the user can provide the list of positions that were changed 
        (mint/burn) over the testing period so that those mints and burns can 
        be simulated)."""

    parser = ArgumentParser(
        description="Fetches a pool's state at a given block.",
        allow_abbrev=False)
    parser.add_argument("pool_address", metavar = "pool address", type = str,
        help = "the address of the relevant Uniswap v3 pool")
    parser.add_argument("block", metavar = "block", type = int,
        help = "the block at which to fetch the pool's state")

    args = parser.parse_args()
    return vars(args)


def main():
    """Fetches a pool's state at a given block.

        Uses web3py and the Uniswap v3 pool ABI to fetch a pool's state at a 
        given block. The pool's state is returned as a dictionary containing 
        the pool's slot0, fee growth global, protocol fees, liquidity and 
        oracle observations. It contains part of the pool's tick-indexed state 
        (specifically it contains 300 tick's worth of data on either side of 
        the current tick at the specified block unless this value is overridden
        by the user). It contains part of the pools position-indexed state 
        (specifically it contains the information for each of the positions 
        specified in the positions list provided by the user - the idea being 
        that the user can provide the list of positions that were changed 
        (mint/burn) over the testing period so that those mints and burns can 
        be simulated).
    """

    try:
        args = parse_args()
        data = fetch_uniswap_transactions_in_range(
            args['pool_address'], args['start_date'], args['end_date'])
        print(data)

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
