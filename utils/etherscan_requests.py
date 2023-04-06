""" Provides basic functions that make requests from the Etherscan API

    Etherscan is the leading blockchain explorer, search, API and analytics 
    platform for Ethereum.
"""


#-----------------------------------------------------------------------
# etherscan_requests.py
# Author: Chris Aubin
#-----------------------------------------------------------------------


import requests
import json


#-----------------------------------------------------------------------


ETHERSCAN_API_KEY      = "I88M79P2XDJ59V8NRKJ4F2UZGNU7E7E756"
ETHERSCAN_API_ENDPOINT = "https://api.etherscan.io/api"


def get_block_no_by_time(timestamp, closest):
    """Gets the Ethereum block mined nearest to the specified time.

    Uses the Etherscan API to fetch the Ethereum mainnet block mined nearest to
    the specified time. The endpoint's documentation can be found here: 
    https://docs.etherscan.io/api-endpoints/blocks#get-block-number-by-timestamp

    Keyword arguments:
    timestamp -- the integer representation the Unix timestamp in seconds
    closest   -- either "before" or "after", to indicate whether the function 
                 should return the closest block before or after the provided 
                 timestamp
    """

    params = {  
        "module":    "block",  
        "action":    "getblocknobytime",
        "timestamp": timestamp,
        "closest":   closest,
        "apikey":    ETHERSCAN_API_KEY,  
    }  

    response      = requests.get(ETHERSCAN_API_ENDPOINT, params = params)
    response_json = json.loads(response.text)

    if response_json["message"] != "OK":
      raise Exception("Error! No closest block found. Likely invalid timestamp.")
    else:
      return int(response_json["result"])


def get_pool_logs(address, from_block, to_block, page = 1):
    """"Gets the logs for particular address in a particular block range.

    Uses the Etherscan API to fetch the logs for particular address in a 
    particular block range. The endpoint's documentation can be found here:
    https://docs.etherscan.io/api-endpoints/logs#get-event-logs-by-address
    
    Keyword arguments:
    address    -- the address of the contract to fetch logs for
    from_block -- the block number to start fetching logs from
    to_block   -- the block number to stop fetching logs from
    """

    params = {  
        "module":    "logs",  
        "action":    "getLogs",
        "address":   address,  
        "apikey":    ETHERSCAN_API_KEY,  
        "fromBlock": from_block,
        "toBlock":   to_block,
        "page":      page,
        "offset":    1000,
    }  

    response      = requests.get(ETHERSCAN_API_ENDPOINT, params = params)
    response_json = json.loads(response.text)
    
    if response_json["message"] != "OK":
        raise Exception("Error! No logs found. Likely incorrect address.")
    else:
        return response_json["result"]