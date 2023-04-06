""" Gets the addresses that called mint/ burn in given events.

    Given a json object containing mints/burns/swaps (typically those for a 
    particular pool in a particular date range), prints the addresses called 
    the mint or burn methods.
"""


#-----------------------------------------------------------------------
# relevant_positions.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import json

from argparse import ArgumentParser
from Crypto.Hash import keccak, encode_packed


#-----------------------------------------------------------------------


def get_relevant_positions(decoded_events):
    """Gets the addresses that called mint/ burn in decoded events """

    positions = set()
    for event in decoded_events["data"]:
        if event["method"] in ["MINT", "BURN"]:
            # The key in a pool's position-indexed state is the keccak256 hash 
            # of the position's owner address and the position's tick range.
            # Non-standard packed encoding is used for the hash, see:
            # keccak256(abi.encodePacked(owner, tickLower, tickUpper))
            # https://github.com/Uniswap/v3-core/blob/d8b1c635c275d2a9450bd6a78f3fa2484fef73eb/contracts/libraries/Position.sol#L36
            # So we need to use the corresponding method from eth_abi:
            # https://eth-abi.readthedocs.io/en/latest/encoding.html
            position_key_encoded = encode_packed( ["address", "int24", "int24"],
                [event["method_data"]["owner"], 
                event["method_data"]["tickLower"], 
                event["method_data"]["tickUpper"]])
            position_keccak = keccak.new(digest_bits = 256)
            position_keccak.update(position_key_encoded)
            addresses.add(position_keccak)
    
    return positions


def parse_args():
    """Parses the command-line arguments."""

    description = """Given a json object containing mints/burns/swaps 
    (typically those for a particular pool in a particular date range), 
    prints the addresses called the mint or burn methods."""

    parser = ArgumentParser(description = description, allow_abbrev = False)
    parser.add_argument("path_to_decoded_events", 
        metavar = "path to decoded events", type = str,
        help = "path to a file containing decoded events")

    args = parser.parse_args()
    return vars(args)


def main():
    """Prints the addresses that called mint/burn.
    
    Given a json object containing mints/burns/swaps (typically those for a 
    particular pool in a particular date range), prints the addresses called 
    the mint or burn methods.
    """

    try:
        args = parse_args()
        decoded_events = json.load(open(args["path_to_decoded_events"], "r"))
        data = get_relevant_addresses(decoded_events)
        print(data)

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
