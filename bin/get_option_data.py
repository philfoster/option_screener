#! /usr/bin/python3

import argparse
import datetime as dt
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"

def main(config_file,symbol,expiration):
    # Get a Market object
    option_chain = get_option_chain(config_file, symbol, expiration)
    print(json.dumps(option_chain.get_option_data()))

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-e','--expiration', dest='expiration', required=False,default=None,help="Expiration Date <YYYY-MM-DD>" )

    expiration = None
    args = parser.parse_args()

    if args.expiration is not None:
        (y,m,d) = args.expiration.split("-")
        expiration = dt.datetime(year=int(y),month=int(m), day=int(d))

    main(args.config_file,args.symbol,expiration)
