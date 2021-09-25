#! /usr/bin/python3

import argparse
import datetime as dt
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"

def main(config_file,symbol,expiration):
    # Get a Market object
    option_chain = get_option_chain(config_file, symbol, expiration)
    for strike_price in option_chain.get_strike_prices():
        call = option_chain.get_call_option(strike_price)
        put = option_chain.get_put_option(strike_price)
        print(f"{call.get_display_symbol()} bid={call.get_bid()} ask={call.get_ask()} io={call.get_open_interest()}")
        print(f"{put.get_display_symbol()} bid={put.get_bid()} ask={put.get_ask()} io={put.get_open_interest()}")

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
