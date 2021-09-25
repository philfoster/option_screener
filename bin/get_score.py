#! /usr/bin/python3

import argparse
from screener_tools import *

DEFAULT_SCREENER_CONFIG_FILE="./etc/stock_screener.json"

def main(screener_config_file,symbol):
    screener_config = read_json_file(screener_config_file)
    score = get_score(screener_config,symbol)
    print(f"{symbol.upper()} score: {score:.2f}%")


if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="screener configuration file", default=DEFAULT_SCREENER_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=False,default=None,help="Perform fresh screen of a symbol")

    args = parser.parse_args()
    main(args.config_file,args.symbol)

