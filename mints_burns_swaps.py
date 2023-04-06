""" Fetches a pool's mints, burns and swaps using Etherscan API

    This module fetches all events that change the liquidity of a particular 
    pool. It uses the Etherscan API (https://docs.etherscan.io). Etherscan is 
    the leading blockchain explorer, search, API and analytics platform for 
    Ethereum. It also uses the PyCryptodome library 
    (https://www.pycryptodome.org) for computing keccak hashes. It also uses 
    the eth_abi package (https://eth-abi.readthedocs.io/en/latest/index.html) 
    that is used internally by web3py.
"""


#-----------------------------------------------------------------------
# mints_burns_swaps.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import datetime
import json
import sys
import time

from argparse import ArgumentParser
from Crypto.Hash import keccak
from eth_abi import decode
from eth_utils import to_checksum_address
from utils.etherscan_requests import get_block_no_by_time, get_pool_logs


#-----------------------------------------------------------------------


# For each relevant Uniswap function:
# 1) Compute and store the keccak hash of the event arguments (in hex). 
#    The first entry in the topics array in an event log is the keccak hash 
#    of the  event arguments, so this can be used to identify the relevant 
#    event logs amongst all of a pools logs.
# 2) Store an array of the function's non-indexed parameters
#    This can be used to decode the data field in the event log using the 
#    eth_abi decode function. 
mint_keccak = keccak.new(digest_bits = 256)
mint_keccak.update(b"Mint(address,address,int24,int24,uint128,uint256,uint256)")
mint_hash  = "0x" + mint_keccak.hexdigest()
mint_types = ["address", "uint128", "uint256", "uint256"]

burn_keccak = keccak.new(digest_bits = 256)
burn_keccak.update(b"Burn(address,int24,int24,uint128,uint256,uint256)")
burn_hash  = "0x" + burn_keccak.hexdigest()
burn_types = ["uint128", "uint256", "uint256"]

swap_keccak = keccak.new(digest_bits = 256)
swap_keccak.update(b"Swap(address,address,int256,int256,uint160,uint128,int24)")
swap_hash  = "0x" + swap_keccak.hexdigest()
swap_types = ["int256", "int256", "uint160", "uint128", "int24"]

def remove_address_padding(address_padded):
    """Removes the padding from an address
    
    Addresses returned by the Etherscan API are padded such that they are 64
    characters long, excluding the "0x". Ethereum addresses are 20 bytes long
    (40 characters in hex), excluding the "0x". This function removes the 
    padding from addresses returned by the Etherscan API.
    """

    address = address_padded[len(address_padded)-40:]
    address = "0x" + address
    return address

def decode_mint(event):
    """Decodes mint events """

    # Use the eth_abi package to decode the data field in the event log
    # using the non-indexed parameters of the mint function
    data_bytes  = bytes.fromhex(event["data"][2:])
    method_data = decode(mint_types, data_bytes)

    # Indexed paramters
    # All addresses returned by the Etherscan API need to be converted to 
    # checksummed addresses for use with the web3py library.    
    owner      = to_checksum_address(remove_address_padding(event["topics"][1]))
    tick_lower = int(event["topics"][2][2:], 16)
    tick_upper = int(event["topics"][3][2:], 16)

    # Non-indexed parameters
    # All addresses returned by the Etherscan API need to be converted to 
    # checksummed addresses for use with the web3py library.    
    sender  = to_checksum_address(remove_address_padding(method_data[0]))
    amount  = method_data[1]
    amount0 = method_data[2]
    amount1 = method_data[3]

    return {
        "sender": sender, 
        "owner": owner, 
        "tickLower": tick_lower, 
        "tickUpper": tick_upper, 
        "amount": amount, 
        "amount0": amount0, 
        "amount1": amount1
        }


def decode_burn(event):
    """Decodes burn events"""

    # Use the eth_abi package to decode the data field in the event log
    # using the non-indexed parameters of the burn function
    data_bytes  = bytes.fromhex(event["data"][2:])
    method_data = decode(burn_types, data_bytes)

    # Indexed paramters
    # All addresses returned by the Etherscan API need to be converted to 
    # checksummed addresses for use with the web3py library.    
    owner      = to_checksum_address(remove_address_padding(event["topics"][1]))
    tick_lower = int(event["topics"][2][2:], 16)
    tick_upper = int(event["topics"][3][2:], 16)

    # Non-indexed parameters
    amount  = method_data[0]
    amount0 = method_data[1]
    amount1 = method_data[2]

    return {
        "owner": owner, 
        "tickLower": tick_lower, 
        "tickUpper": tick_upper, 
        "amount": amount, 
        "amount0": amount, 
        "amount1": amount1
        }


def decode_swap(event):
    """Decodes swap events"""

    # Use the eth_abi package to decode the data field in the event log
    # using the non-indexed parameters of the swap function
    data_bytes  = bytes.fromhex(event['data'][2:])
    method_data = decode(swap_types, data_bytes)

    # Indexed paramters
    # All addresses returned by the Etherscan API need to be converted to 
    # checksummed addresses for use with the web3py library.    
    sender    = to_checksum_address(remove_address_padding(event['topics'][1]))
    recipient = to_checksum_address(remove_address_padding(event['topics'][2]))

    # Non-indexed parameters
    amount0       = method_data[0]
    amount1       = method_data[1]
    sqrt_priceX96 = method_data[2]
    liquidity     = method_data[3]
    tick          = method_data[4]

    return {
        "sender": sender, 
        "recipient": recipient, 
        "amount0": amount0, 
        "amount1": amount1, 
        "sqrtPriceX96": sqrt_priceX96, 
        "liquidity": liquidity, 
        "tick": tick
        }


def decode_uniswap_event(event):
    """Decodes Uniswap event logs"""

    # Convert hex values to decimal values
    block_no  = int(event["blockNumber"], 16)
    timestamp = int(event["timeStamp"], 16)
    gas_price = int(event["gasPrice"], 16)
    gas_used  = int(event["gasUsed"], 16)

    # Calculate gas used in eth (note - not geth)
    gas_total = gas_price * 10**(-18) * gas_used

    # Decode event
    if (event["topics"][0]) == mint_hash:
        method      = "MINT"
        method_data = decode_mint(event)
    elif (event["topics"][0]) == burn_hash:
        method      = "BURN"
        method_data = decode_burn(event)
    elif (event["topics"][0]) == swap_hash:
        method      = "SWAP"
        method_data = decode_swap(event)
    else:
        raise Exception("Error! Can only decode mint, burn and swap events.")

    return {
        "blockNo": block_no, 
        "timestamp": timestamp, 
        "gasPrice": gas_price, 
        "gasUsed": gas_used, 
        "gasTotal": gas_total, 
        "method": method, 
        "method_data": method_data
        }


def fetch_uniswap_transactions_in_range(pool_address, start_date, end_date):
    """Fetches and decodes all mints, burns and swaps for pool in date range

    Keyword arguments:
    pool_address -- the address of the uniswap pool
    start_date   -- the start date (dd/mm/yyyy)
    end_date     -- the end date (dd/mm/yyyy)
    """
    
    start_timestamp = int(time.mktime(datetime.datetime.strptime(start_date, "%d/%m/%Y").timetuple()))
    end_timestamp   = int(time.mktime(datetime.datetime.strptime(end_date, "%d/%m/%Y").timetuple()))

    start_block = get_block_no_by_time(start_timestamp, "after")
    end_block   = get_block_no_by_time(end_timestamp, "before")

    logs = get_pool_logs(pool_address, start_block, end_block)

    decoded_transactions = []

    for event in logs:
        if event["topics"][0] in [mint_hash, burn_hash, swap_hash]:
            decoded_transactions.append(decode_uniswap_event(event))
    
    return {"data": decoded_transactions}


def parse_args():
    """Parses the command-line arguments."""

    description = """Given a pool's address and a start and end date, fetches 
    the pool's mints, burns and swaps in the date range using Etherscan API."""

    parser = ArgumentParser(description = description, allow_abbrev = False)
    parser.add_argument("pool_address", metavar = "pool address", type = str,
        help = "the address of the relevant Uniswap v3 pool")
    parser.add_argument("start_date", metavar = "start date", type = str,
        help = "the start of the date range (dd/mm/yyyy)")
    parser.add_argument("end_date", metavar="end date", type = str,
        help = "the end of the date range (dd/mm/yyyy)")

    args = parser.parse_args()
    return vars(args)


def main():
    """Prints the mint/burns/swaps for a uniswap pool.
    
    Given a pool's address and a start and end date, fetches the pool's mints, 
    burns and swaps in the date range using Etherscan API.
    """
    
    try:
        args = parse_args()
        data = fetch_uniswap_transactions_in_range(
            args['pool_address'], args['start_date'], args['end_date'])
        print(json.dumps(data, indent = 4))

    except Exception as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
