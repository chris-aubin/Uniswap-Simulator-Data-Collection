""" Gets the average gas used to call each uniswap method in given events

    Given a json object containing mints/burns/swaps/flashes/ (typically those 
    for a particular pool in a particular date range), prints the average gas 
    used to call each of those methods. If a particular event doesn't occur,
    prints -1.
"""


#-----------------------------------------------------------------------
# gas_estimates.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import json
import sys

from argparse import ArgumentParser


def get_mint_burn_swap_gas_estimates(decoded_events):
    """Calculates the average gas used to call each uniswap method."""

    mint_av       = 0
    mint_count    = 0
    burn_av       = 0
    burn_count    = 0
    swap_av       = 0
    swap_count    = 0
    flash_av      = 0
    flash_count   = 0
    collect_av    = 0
    collect_count = 0

    for event in decoded_events:
        if event["method"] == "MINT":
            mint_av    += event["gasUsed"]
            mint_count += 1
        elif event["method"] == "BURN":
            burn_av    += event["gasUsed"]
            burn_count += 1
        elif event["method"] == "SWAP":
            swap_av    += event["gasUsed"]
            swap_count += 1
        elif event["method"] == "FLASH":
            flash_av    += event["gasUsed"]
            flash_count += 1
        elif event["method"] == "COLLECT":
            collect_av    += event["gasUsed"]
            collect_count += 1

    avs = {}
    if mint_count != 0:
        mint_av = mint_av / mint_count
        avs["mintAv"] = mint_av
    else:
        avs["mintAv"] = -1

    if burn_count != 0:
        burn_av = burn_av / burn_count
        avs["burnAv"] = burn_av
    else:
        avs["burnAv"] = -1

    if swap_count != 0:
        swap_av = swap_av / swap_count
        avs["swapAv"] = swap_av
    else:
        avs["swapAv"] = -1

    if flash_count != 0:
        flash_av = flash_av / flash_count
        avs["flashAv"] = flash_av
    else:
        avs["flashAv"] = -1

    if collect_count != 0:
        collect_av = collect_av / collect_count
        avs["collectAv"] = collect_av
    else:
        avs["collectAv"] = -1

    return avs


def parse_args():
    """Parses the command-line arguments."""

    description = """Given a json object containing mints/burns/swaps/flashes/
    collects (typically those for a particular pool in a particular date range), 
    prints the average gas used to call each of those methods. If a particular 
    event doesn't occur, prints -1."""

    parser = ArgumentParser(description = description, allow_abbrev = False)
    parser.add_argument("path_to_decoded_events", type = str,
        help = "path to a file containing decoded events")

    args = parser.parse_args()
    return vars(args)


def main():
    """Prints the average gas used to call mint/burn/swap/flash/collect.
    
    Given a json object containing mints/burns/swaps/flashes/ (typically those 
    for a particular pool in a particular date range), prints the average gas 
    used to call each of those methods. If a particular event doesn't occur,
    prints -1.
    """

    try:
        args = parse_args()
        decoded_events = json.load(open(args["path_to_decoded_events"], "r"))
        gas_estimates = get_mint_burn_swap_gas_estimates(decoded_events["data"])
        data = {}
        data["poolAddress"] = decoded_events["poolAddress"]
        data["startDate"] = decoded_events["startDate"]
        data["endDate"] = decoded_events["endDate"]
        data["startBlock"] = decoded_events["startBlock"]
        data["endBlock"] = decoded_events["endBlock"]
        data["data"] = gas_estimates
        print(json.dumps(data, indent = 4))

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
