#! /usr/bin/python3

import argparse
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"

def main(config_file,symbol,verbose):
    # Get a Market object
    quote = get_quote(config_file, symbol)
    if verbose:
        print(f"{symbol} ({quote.get_company_name()})")
        print(f"\tPrice : ${quote.get_price():.2f} " + 
                f"bid=${quote.get_bid():.2f}({quote.get_bid_size()}) " +
                f"ask=${quote.get_ask():.2f}({quote.get_ask_size()})")
        print(f"\tVolume: {quote.get_volume()} (avg={quote.get_average_volume()})")
    else:
        print(f"{symbol} = {quote.get_price()}")

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    args = parser.parse_args()
    main(args.config_file,args.symbol,args.verbose)
