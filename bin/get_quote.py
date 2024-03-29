#! /usr/bin/python3

import argparse
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"
DEFAULT_SCREENER_CONFIG_FILE="./etc/stock_screener.json"

def main(config_file,screener_config_file,symbol,verbose):
    # Get a Market object
    
    screener_config = read_json_file(screener_config_file)
    quote = get_quote(config_file, symbol, screener_config=screener_config)
    sector = quote.get_sector()
    if verbose:
        if sector:
            print(f"{symbol} ({quote.get_company_name()}/{sector})")
        else:
            print(f"{symbol} ({quote.get_company_name()})")
        print(f"\tPrice     : ${quote.get_price():.2f} / ${quote.get_change_close():.2f} ({quote.get_change_close_prct():.2f}%)")
        print(f"\tDay Range : ${quote.get_day_low():.2f} - ${quote.get_day_low()}")
        print(f"\tBid       : ${quote.get_bid():.2f} ({quote.get_bid_size()})")
        print(f"\tAsk       : ${quote.get_ask():.2f} ({quote.get_ask_size()})")
        print("\nCompany details")
        print(f"\tVolume       : {quote.get_volume()} (avg={quote.get_average_volume()})")
        print(f"\t52 Week High : ${quote.get_52week_high():.2f} ({quote.get_52week_high_date()})")
        print(f"\t52 Week Low  : ${quote.get_52week_low():.2f} ({quote.get_52week_low_date()})")
        print(f"\tMarketCap    : ${quote.get_market_cap()}")
        print(f"\tFloat        : {quote.get_float()} shares")
        print(f"\tBeta         : {quote.get_beta()}")
        print(f"\tEarningsDate : {quote.get_next_earnings_date()}")
    else:
        print(f"{symbol}: ${quote.get_price():.2f} / ${quote.get_change_close():.2f} ({quote.get_change_close_prct():.2f}%)")

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--screener-config', dest='screener_config_file', help="etrade configuration file", default=DEFAULT_SCREENER_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    args = parser.parse_args()
    main(args.config_file,args.screener_config_file,args.symbol,args.verbose)
