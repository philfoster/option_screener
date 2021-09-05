#! /usr/bin/python3

import argparse
import os
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"
DEFAULT_SCREENER_CONFIG_FILE="stock_screener.json"

CACHE_DIR="cache_dir"
CACHE_VALUE="value"
SECTOR_QUESTION_ID="sector_question_id"

def main(config_file,screener_config_file,symbol,verbose):
    # Get a Market object
    quote = get_quote(config_file, symbol)
    sector = get_sector(screener_config_file,symbol)
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
    else:
        print(f"{symbol}: ${quote.get_price():.2f} / ${quote.get_change_close():.2f} ({quote.get_change_close_prct():.2f}%)")

def get_sector(screener_config_file,symbol):
    screener_config = read_json_file(screener_config_file)

    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    if not os.path.exists(expanduser(answer_file)):
        return None

    sector_question_id = screener_config.get(SECTOR_QUESTION_ID,None)
    if sector_question_id is None:
        return None

    answers = get_all_answers_from_cache(answer_file)
    answer = answers.get(sector_question_id,None)
    if answer:
        return answer.get(CACHE_VALUE,None)
    return None

def get_all_answers_from_cache(cache_file):
    answers = dict()
    try:
        answers = read_json_file(cache_file)
    except Exception as e:
        pass
    return answers

def get_answer_file(cache_dir,symbol):
    return f"{cache_dir}/{symbol.upper()}.json"

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('--screener-config', dest='screener_config_file', help="etrade configuration file", default=DEFAULT_SCREENER_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    args = parser.parse_args()
    main(args.config_file,args.screener_config_file,args.symbol,args.verbose)
