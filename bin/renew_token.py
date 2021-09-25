#! /usr/bin/python3

import argparse
from etrade_tools import *
DEFAULT_CONFIG_FILE="./etc/etrade.json"

def main(config_file,force_renew):
    renew_authtoken(config_file,force_renew)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)

    args = parser.parse_args()
    force_renew = True
    main(args.config_file,force_renew)
