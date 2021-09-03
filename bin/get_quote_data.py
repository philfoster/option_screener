#! /usr/bin/python3

import argparse
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"

def main(config_file,symbol):
    # Get a Market object
    quote_data = get_quote_data(config_file, symbol)
    print(json.dumps(quote_data))

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    args = parser.parse_args()
    main(args.config_file,args.symbol)
