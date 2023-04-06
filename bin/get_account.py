#! /usr/bin/python3

import argparse
import json
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"

def main(config_file, verbose):
    accounts = get_account_list(config_file)
    rollover = accounts.get_account_by_name("Rollover IRA")
    if rollover:
        print(f"Account {rollover.get_name()}")

        for p in rollover.get_positions():
            quantity = p.get_quantity()
            print(f"{p.get_display_name()} quantity={quantity}")

        print(f"Cash: ${rollover.get_balance():.2f}")

    


if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    args = parser.parse_args()
    main(args.config_file,args.verbose)

