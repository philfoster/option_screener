#! /usr/bin/python3

import argparse
import json
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"
DEFAULT_ACCOUNT_NAME="Rollover IRA"

def main(config_file, account_name):
    acct = get_account_by_name(config_file, account_name)
    print(f"acct name={acct.get_display_name()} balance=${acct.get_balance():.2f}")

def get_account_by_name(config_file, account_name):
    accounts = get_account_list(config_file)
    return accounts.get_account_by_name(account_name)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-a','--account', dest='account_name', required=False,default=DEFAULT_ACCOUNT_NAME,action='store_true',help="Account Name")
    args = parser.parse_args()
    main(args.config_file,args.account_name)

