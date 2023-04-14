""" Plots a pool's liquidity.

    Plots the liquidity for a given pool state (using output of pool_state.py).
"""


#-----------------------------------------------------------------------
# plot_liquidity.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import json
import math
import matplotlib.pyplot as plt
import numpy as np
import sys

from argparse import ArgumentParser


#-----------------------------------------------------------------------


MIN_TICK                  = -887272
MAX_TICK                  = 887272


def get_liquidity_per_tick(initialized_ticks, current_tick, tick_spacing, liquidity):
    """Given the tick-indexed state of a pool, gets the liquidity for each tick.
    
    The tick-indexed state of a pool does not store the active liquidity at 
    each tick, rather it stores how much the active liquidity changes when
    crossing a tick. This function computes the active liquidity at each tick.

    Keyword arguments:
    initialized_ticks -- the tick-indexed state of the pool
    current_tick      -- the current tick of the pool
    tick_spacing      -- the tick spacing of the pool
    liquidity         -- the current liquidity of the pool
    """

    # The pools current tick isn't necessarily a tick that can actually be 
    # initialized. Only ticks that are divisible by tick_spacing can be 
    # initialized. So we need to find the nearest initializable tick using the 
    # tick spacing.
    current_tick_idx = current_tick
    active_tick_idx = math.floor(current_tick_idx / tick_spacing) * tick_spacing
    if active_tick_idx < MIN_TICK:
        active_tick_idx = MIN_TICK
    elif active_tick_idx > MAX_TICK: 
        active_tick_idx = MAX_TICK

    # Store active tick"s liqudity data for use in computeSurroundingTicks 
    # function
    active_tick_processed = {
        "liquidity_active": liquidity,
        "tick_idx": active_tick_idx,
        "liquidity_net": 0,
        "liquidity_gross": 0,
    }

    # If our active tick happens to be initialized (i.e. there is a position 
    # that starts or ends at that tick), ensure we set the gross and net 
    # liquidities.
    if active_tick_idx in initialized_ticks:
        active_tick = initialized_ticks[active_tick_idx]
        active_tick_processed["liquidity_gross"] = active_tick["liquidityGross"]
        active_tick_processed["liquidity_net"] = active_tick["liquidityNet"]

    num_surrounding_ticks = 300

    # Computes the liquidity information at each tick within 
    # num_surrounding_ticks above or below the active tick. Necessary because 
    # the liquidityActive for each tick returned by the subgraph is only the 
    # liquidity of positions that start or end at the tick (it does not account
    #  for any liquidity as a result of positions that contain the tick).
    def compute_surrounding_ticks(active_tick_processed, tick_spacing, direction): 
        processed_ticks         = []
        processed_ticks.append(active_tick_processed)
        current_tick_idx        = active_tick_processed["tick_idx"]
        previous_tick_processed = active_tick_processed
        
        # Iterate outwards (either up or down depending on "Direction") from 
        # the active tick, building active liquidity for every tick.
        for i in range(num_surrounding_ticks):
            if direction == "ASC":
                current_tick_idx += tick_spacing
            elif direction == "DSC":
                current_tick_idx -= tick_spacing
            else:
                raise Exception("Invalid direction " + direction + ":")

            if (current_tick_idx < MIN_TICK or current_tick_idx > MAX_TICK):
                break

            current_tick_processed = {
                "liquidity_active": previous_tick_processed["liquidity_active"],
                "tick_idx":         current_tick_idx,
                "liquidity_net":    0,
                "liquidity_gross":  0,
            }

            current_tick_initialized = current_tick_idx in initialized_ticks
            # Check if there is an initialized tick at our current tick.
            # If so copy the gross and net liquidity from the initialized tick.
            if current_tick_initialized:
                current_initialized_tick                  = initialized_ticks[current_tick_idx]
                current_tick_processed["liquidity_gross"] = current_initialized_tick["liquidityGross"]
                current_tick_processed["liquidity_net"]   = current_initialized_tick["liquidityNet"]

            # Update the active liquidity.
            # If we are iterating ascending and we found an initialized tick we 
            # immediately apply it to the current processed tick we are building.
            # If we are iterating descending, we don"t want to apply the net 
            # liquidity until the following tick. Recall liquidityNet is the amount
            # of net liquidity added when tick is crossed from left to right, or 
            # subtracted when the tick is crossed from right to left.
            if (direction == "ASC" and current_tick_initialized): 
                current_tick_processed["liquidity_active"] = previous_tick_processed["liquidity_active"] + current_initialized_tick["liquidityNet"]
            elif (direction == "DSC" and previous_tick_processed["liquidity_net"] != 0):
                # We are iterating descending, so look at the previous tick and 
                # apply any net liquidity.
                current_tick_processed["liquidity_active"] = previous_tick_processed["liquidity_active"] - current_initialized_tick["liquidityNet"]

            processed_ticks.append(current_tick_processed)
            previous_tick_processed = current_tick_processed

        return processed_ticks

    subsequent_ticks = compute_surrounding_ticks(
        active_tick_processed,
        tick_spacing,
        "ASC"
    )

    previous_ticks = compute_surrounding_ticks(
        active_tick_processed,
        tick_spacing,
        "DSC"
    )

    ticks_processed = previous_ticks + subsequent_ticks

    return {
        "data": {
        "ticks_processed": ticks_processed,
        "tick_spacing": tick_spacing,
        "active_tick_idx": active_tick_idx,
        },
    }


def plot_liquidity(liquidity_per_tick):
    """Plots the provided liquidity.
    
    Keyword arguments:
    liquidity_per_tick -- the liquidity to plot
    """

    data = {}
    for tick in liquidity_per_tick["data"]["ticks_processed"]:
        tick_idx = tick["tick_idx"]
        liquidity_active = tick["liquidity_active"]
        data[tick_idx] = liquidity_active

    ticks = list(data.keys())
    liquidities = list(data.values())

    plt.bar(ticks, liquidities, color = "maroon",
        width = 100)
 
    plt.show()


def parse_args():
    """Parses the command-line arguments."""

    description = """Plots the liquidity for a given pool state (the output of 
        pool_state.py)."""

    parser = ArgumentParser(description=description, allow_abbrev=False)
    parser.add_argument("path_to_pool_state", type = str,
        help = "path to a file containing pool state")

    args = parser.parse_args()
    return vars(args)


def main():
    """Plots a pool's liquidity.

    Plots the liquidity for a given pool state (using output of pool_state.py).
    """

    try:
        args = parse_args()
        pool_state = json.load(open(args["path_to_pool_state"], "r"))
        ticks_temp = pool_state["data"]["ticks"]
        ticks = {}
        for tick_idx in ticks_temp:
            ticks[int(tick_idx)] = ticks_temp[tick_idx] 
        current_tick_idx = pool_state["data"]["slot0"]["tick"]
        tick_spacing = pool_state["data"]["tickSpacing"]
        liquidity = pool_state["data"]["liquidity"]
        liquidity_per_tick = get_liquidity_per_tick(ticks, current_tick_idx, tick_spacing, liquidity)
        plot_liquidity(liquidity_per_tick)
        print(json.dumps(liquidity_per_tick, indent = 4))

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()