#! /usr/bin/python3

import argparse
import datetime
import sys
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"
DEFAULT_SCREENER_CONFIG="./etc/stock_screener.json"

DEFAULT_MAX_COST=100000
DEFAULT_MIN_ANNUALIZED=48

DEFAULT_LONG_CALL_MIN_DAYS = 7 * 20
DEFAULT_LONG_CALL_MAX_DAYS = 7 * 56
DEFAULT_SHORT_CALL_MIN_DAYS = 1
DEFAULT_SHORT_CALL_MAX_DAYS = 7 * 4

global GLOBAL_DEBUG
global GLOBAL_VERBOSE

def main(config_file, screener_config, symbol, max_cost, min_annualized, long_call_min_days, long_call_max_days, short_call_min_days, short_call_max_days):
    quote = get_quote(config_file, symbol)
    price = quote.get_price()

    # Long call strike range is 45% to 70% of the cost
    long_call_min_strike = price * 0.45
    long_call_max_strike = price * 0.7

    long_option_chain_list = get_matching_option_chains(config_file, symbol, long_call_min_days, long_call_max_days)
    short_option_chain_list = get_matching_option_chains(config_file, symbol, short_call_min_days, short_call_max_days)

    today = datetime.datetime.now()

    for long_option_chain in long_option_chain_list:
        long_call_expiration = long_option_chain.get_expiration()
        for long_strike in long_option_chain.get_strike_prices():
            if long_call_min_strike <= long_strike <= long_call_max_strike:
                long_call = long_option_chain.get_call_option(long_strike)
                long_call_ask = long_call.get_ask()
                long_time_value = (long_strike + long_call_ask) - price
                #print(f"examining {long_call_expiration} strike {long_strike}: time value ${long_time_value:.2f}")

                # Loop through the short strikes
                for short_option_chain in short_option_chain_list:
                    short_call_expiration = short_option_chain.get_expiration()
                    short_dte = short_option_chain.get_expiration() - today
                    for short_strike in short_option_chain.get_strike_prices():
                        if short_strike > price:
                            short_call = short_option_chain.get_call_option(short_strike)
                            short_call_bid = short_call.get_bid()
                            if short_call_bid > long_time_value:
                                cost_basis = long_strike + long_call_ask - short_call_bid
                                out_of_pocket = long_call_ask - short_call_bid
                                max_gain = short_strike - cost_basis
                                gain_prct = 100 * ( max_gain / out_of_pocket )
                                annualized_gain = gain_prct * (365 /short_dte.days)
                                if annualized_gain >= min_annualized and out_of_pocket <= max_cost:
                                    if GLOBAL_VERBOSE:
                                        print(f"long call: {long_call.get_display_symbol()} (time_value={long_time_value:.2f}) short call {short_call.get_display_symbol()} (bid={short_call_bid:.2f}) days={short_dte.days}")
                                        print(f"    cost_basis = ${cost_basis:.2f} my cost=${out_of_pocket:.2f} max_gain=${max_gain:.2f} ({gain_prct:.1f}%) annualized={annualized_gain:.2f}%)")
                                    else:
                                        print(f"{long_call.get_display_symbol()} / {short_call.get_display_symbol()} cost=${out_of_pocket*100:.2f} max_gain=${max_gain:.2f}({gain_prct:.1f}%) days={short_dte.days} annualized={annualized_gain:.2f}%")
                                else:
                                    debug(f"TOO LOW: {long_call.get_display_symbol()} / {short_call.get_display_symbol()} cost=${out_of_pocket*100:.2f} max_gain=${max_gain:.2f}({gain_prct:.1f}%) days={short_dte.days} annualized={annualized_gain:.2f}%")
                            else:
                                debug(f"PREMIUMS DO NOT MATCH: {long_call.get_display_symbol()} / {short_call.get_display_symbol()} time_value={long_time_value}, short call bid={short_call_bid}")

def get_matching_option_chains(config_file, symbol, min_days, max_days):
    option_chain_list = list()

    today = datetime.datetime.now()
    dates = get_expiration_dates(config_file, symbol)

    for (expiration_date, expiration_type) in dates:
        elapsed = expiration_date - today
        days = elapsed.days
        if min_days < days < max_days:
            option_chain = get_option_chain(config_file, symbol, expiration_date)
            if option_chain:
                option_chain_list.append(option_chain)

    return option_chain_list

def get_expiration_dates(config_file, symbol):
    date_list = list()
    dates_data = get_options_expiration_dates(config_file, symbol)
    for date in dates_data.get("OptionExpireDateResponse").get("ExpirationDate"):
        year = date.get("year")
        month = date.get("month")
        day = date.get("day")
        expiration = datetime.datetime(year=int(year),month=int(month), day=int(day))
        date_list.append((expiration,date.get("expiryType")))
    return date_list
    
def debug(msg):
    if GLOBAL_DEBUG:
        print(msg)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', help="Symbol to search (conflicts with -r)" )
    parser.add_argument('-d','--debug', dest='debug_flag', required=False,default=False,action='store_true',help="Enable debugging" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('--max-cost', dest='max_cost', required=False,default=DEFAULT_MAX_COST,help="Max out of pocket cost in dollars")
    parser.add_argument('--min-annualized', dest='min_annualized', required=False,default=DEFAULT_MIN_ANNUALIZED,help="Minimum annualized gain")

    parser.add_argument('--long-call-min-days', dest='long_call_min_days', required=False,default=DEFAULT_LONG_CALL_MIN_DAYS,help="Long call minimum days until expiration")
    parser.add_argument('--long-call-max-days', dest='long_call_max_days', required=False,default=DEFAULT_LONG_CALL_MAX_DAYS,help="Long call maximum days until expiration")
    parser.add_argument('--min-days', '--short-call-min-days', dest='short_call_min_days', required=False,default=DEFAULT_SHORT_CALL_MIN_DAYS,help="Short call minimum days until expiration")
    parser.add_argument('--max-days', '--short-call-max-days', dest='short_call_max_days', required=False,default=DEFAULT_SHORT_CALL_MAX_DAYS,help="Short call maximum days until expiration")

    expiration = None
    args = parser.parse_args()

    GLOBAL_VERBOSE = args.verbose
    GLOBAL_DEBUG = args.debug_flag

    screener_config_file = DEFAULT_SCREENER_CONFIG
    main(
        args.config_file,
        screener_config_file,
        args.symbol,
        int(args.max_cost),
        int(args.min_annualized),
        int(args.long_call_min_days),
        int(args.long_call_max_days),
        int(args.short_call_min_days),
        int(args.short_call_max_days)
        )

