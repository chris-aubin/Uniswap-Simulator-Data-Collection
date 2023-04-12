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


import datetime
import json
import math
import sys
import time

from argparse import ArgumentParser
from utils.uniswap_pool_abi import UNISWAP_POOL_ABI
from utils.etherscan_requests import get_block_no_by_time, get_contract_abi
from web3 import Web3


#-----------------------------------------------------------------------

MIN_TICK                  = -887272
MAX_TICK                  = 887272
DEFAULT_SURROUNDING_TICKS = 300
INFURA_PROVIDER           = "https://mainnet.infura.io/v3/0c7d3f029eb34415866f7e943521f4ee"


def get_pool_state(
        pool_address,
        block,
        positions,
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

    pool_address_checksummed = Web3.to_checksum_address(pool_address)
    # Initialize web3 and the pool contract
    w3                   = Web3(Web3.HTTPProvider(INFURA_PROVIDER))
    w3.eth.default_block = block
    pool                 = w3.eth.contract(address = pool_address_checksummed, abi = UNISWAP_POOL_ABI)

    # Fetch the pool's state by calling the getters that solidity generates
    # automatically for each public state variable.
    token0_address         = Web3.to_checksum_address(pool.functions.token0().call())
    token1_address         = Web3.to_checksum_address(pool.functions.token1().call())
    fee_growth_global0X128 = pool.functions.feeGrowthGlobal0X128().call()
    fee_growth_global1X128 = pool.functions.feeGrowthGlobal1X128().call()
    protocol_fees_raw      = pool.functions.protocolFees().call()
    liquidity              = pool.functions.liquidity().call()
    slot0                  = pool.functions.slot0().call()
    tick_spacing           = pool.functions.tickSpacing().call()

    protocol_fees = {}
    protocol_fees["token0"] = protocol_fees_raw[0]
    protocol_fees["token1"] = protocol_fees_raw[1]

    pool_state = {
        "token0":               token0_address,
        "token1":               token1_address,
        "tickSpacing":          tick_spacing,
        "feeGrowthGlobal0X128": fee_growth_global0X128,
        "feeGrowthGlobal1X128": fee_growth_global1X128,
        "protocolFees":         protocol_fees,
        "liquidity":            liquidity,
        "slot0":                {"sqrtPriceX96": slot0[0], "tick": slot0[1], "observationIndex": slot0[2], "observationCardinality": slot0[3], "feeProtocol": slot0[4]}
    }

    # Fetch the pool's token0 balance
    token0_abi             = get_contract_abi(token0_address)
    token0                 = w3.eth.contract(address=token0_address, abi=token0_abi)
    balance_token0         = token0.functions.balanceOf(pool_address_checksummed).call()
    pool_state["balance0"] = balance_token0

    # Fetch the pool's token1 balance
    token1_abi             = get_contract_abi(token1_address)
    token1                 = w3.eth.contract(address=token1_address, abi=token1_abi)
    balance_token1         = token1.functions.balanceOf(pool_address_checksummed).call()
    pool_state["balance1"] = balance_token1

    # The pools current tick isn't necessarily a tick that can actually be 
    # initialized. Only ticks that are divisible by tick_spacing can be 
    # initialized. So we need to find the nearest initializable tick using the 
    # tick spacing.
    current_tick_idx = pool_state["slot0"]["tick"]
    tick_spacing     = pool_state["tickSpacing"]
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
        observation = {}
        observation_raw = pool.functions.observations(i).call()
        observation["blockTimestamp"]                    = observation_raw[0]
        observation["tickCumulative"]                    = observation_raw[1]
        observation["secondsPerLiquidityCumulativeX128"] = observation_raw[2]
        observation["initialized"]                       = observation_raw[3]
        observations.append(observation)
    pool_state["observations"] = observations

    # Fetch the tick information for the specified number of ticks above 
    # and below the current tick. 
    tick_indexed_state = {}
    tick_idx = active_tick_idx
    for i in range(1, DEFAULT_SURROUNDING_TICKS):
        tick                                   = {}
        tick_idx                               += i*tick_spacing
        tick_raw                               = pool.functions.ticks(tick_idx).call()
        tick["LiquidityGross"]                 = tick_raw[0]
        tick["LiquidityNet"]                   = tick_raw[1]
        tick["FeeGrowthOutside0X128"]          = tick_raw[2]
        tick["FeeGrowthOutside1X128"]          = tick_raw[3]
        tick["tickCumulativeOutside"]          = tick_raw[4]
        tick["secondsPerLiquidityOutsideX128"] = tick_raw[5]
        tick["secondsOutside"]                 = tick_raw[6]
        tick["initialized"]                    = tick_raw[7]
        tick_indexed_state[tick_idx]           = tick
    tick_idx = active_tick_idx
    for i in range(1, DEFAULT_SURROUNDING_TICKS):
        tick                                   = {}
        tick_idx                               -= i*tick_spacing
        tick_raw                               = pool.functions.ticks(tick_idx).call()
        tick["LiquidityGross"]                 = tick_raw[0]
        tick["LiquidityNet"]                   = tick_raw[1]
        tick["FeeGrowthOutside0X128"]          = tick_raw[2]
        tick["FeeGrowthOutside1X128"]          = tick_raw[3]
        tick["tickCumulativeOutside"]          = tick_raw[4]
        tick["secondsPerLiquidityOutsideX128"] = tick_raw[5]
        tick["secondsOutside"]                 = tick_raw[6]
        tick["initialized"]                    = tick_raw[7]
        tick_indexed_state[tick_idx]           = tick
    pool_state["ticks"] = tick_indexed_state

    # Fetch the position information for the positions specified by the user
    position_indexed_state = {}
    for position_key in positions.values():
        position                             = {}
        position_raw                         = pool.functions.positions(position_key).call()
        position["liquidity"]                = position_raw[0]
        position["feeGrowthInside0LastX128"] = position_raw[1]
        position["feeGrowthInside1LastX128"] = position_raw[2]
        position["tokensOwed0"]              = position_raw[3]
        position["tokensOwed1"]              = position_raw[4]
        position_indexed_state[position_key] = position
    pool_state["positions"] = position_indexed_state

    return pool_state
    


def parse_args():
    """Parses the command-line arguments."""

    description = """Uses web3py and the Uniswap v3 pool ABI to fetch a pool's 
        state at a given block. The pool's state is returned as a dictionary 
        containing the pool's slot0, fee growth global, protocol fees, 
        liquidity and oracle observations. It contains part of the pool's 
        tick-indexed state (specifically it contains 300 tick's worth of data 
        on either side of the current tick at the specified block unless this 
        value is overridden by the user). It contains part of the pools 
        position-indexed state (specifically it contains the information for 
        each of the positions specified in the positions list provided by the 
        user - the idea being that the user can provide the list of positions 
        that were changed (mint/burn) over the testing period so that those 
        mints and burns can be simulated)."""

    parser = ArgumentParser(description=description, allow_abbrev=False)
    parser.add_argument("pool_address", type = str,
        help = "the address of the relevant Uniswap v3 pool")
    parser.add_argument("date", type = str,
        help = "the date at which to fetch the pool's state")
    parser.add_argument("path_to_positions", type = str,
        help = "path to a file containing positions")
    parser.add_argument("surrounding_ticks", type = int,
        help = "the number of ticks surrounding the current tick to fetch data for")

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
        positions = json.load(open(args["path_to_positions"], "r"))
        timestamp = int(time.mktime(datetime.datetime.strptime(args["date"], "%d/%m/%Y").timetuple()))
        block = get_block_no_by_time(timestamp, "after")
        data = {}
        pool_state = get_pool_state(
            args["pool_address"], block, positions["data"], args["surrounding_ticks"])
        data["poolAddress"] = args["pool_address"]
        data["block"] = block
        data["data"] = pool_state
        print(json.dumps(data, indent = 4))

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
