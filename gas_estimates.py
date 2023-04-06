""" Gets the average gas used to call each uniswap method in given events

    Given a json object containing mints/burns/swaps (typically those for a 
    particular pool in a particular date range), prints the average gas used to 
    call each of those methods.
"""


#-----------------------------------------------------------------------
# relevant_addresses.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import json
import sys

from argparse import ArgumentParser


def get_mint_burn_swap_gas_estimates(decoded_events):
    """Calculates the average gas used to call each uniswap method."""

    mint_av    = 0
    mint_count = 0
    burn_av    = 0
    burn_count = 0
    swap_av    = 0
    swap_count = 0

    for event in decoded_events:
        if event["method"] == "MINT":
            mint_av    += event["gas_used"]
            mint_count += 1
        elif event["method"] == "BURN":
            burn_av    += event["gas_used"]
            burn_count += 1
        elif event["method"] == "SWAP":
            swap_av    += event["gas_used"]
            swap_count += 1

    mint_av = mint_av / mint_count
    burn_av = burn_av / burn_count
    swap_av = swap_av / swap_count

    return {"mintAv": mint_av, "burnAv": burn_av, "swapAv": swap_av}


def parse_args():
    """Parses the command-line arguments."""

    description = """Given a json object containing mints/burns/swaps 
    (typically those for a particular pool in a particular date range), 
    prints the average gas used to call each of those methods."""

    parser = ArgumentParser(description = description, allow_abbrev = False)
    parser.add_argument("path_to_decoded_events", 
        metavar = "path to decoded events", type = str,
        help = "path to a file containing decoded events")

    args = parser.parse_args()
    return vars(args)


def main():
    """Prints the average gas used to call mint/burn/swap.
    
    Given a json object containing mints/burns/swaps (typically those for a 
    particular pool in a particular date range), prints the average gas used to 
    call each of those methods.
    """

    try:
        args = parse_args()
        decoded_events = json.load(open(args["path_to_decoded_events"], "r"))
        data = get_mint_burn_swap_gas_estimates(decoded_events["data"])
        print(data)

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
