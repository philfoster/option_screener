#! /usr/bin/python3

import argparse
import datetime
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"

DEFAULT_MIN_OPEN_INTEREST=25
DEFAULT_MIN_ANNUAL_ROO=0.0
DEFAULT_MAX_ANNUAL_ROO=2.0
DEFAULT_MIN_ANNUAL_UPSIDE=0.0

DEFAULT_MIN_DOWNSIDE=0.0
DEFAULT_MIN_DELTA=0.0
DEFAULT_MAX_DELTA=1.0

def main(config_file,market_tone_config,symbol,expiration,debug,verbose):
    # Get the market tone config
    tone_config = read_json_file(market_tone_config)

    # Get a Market object
    option_chain = get_option_chain(config_file, symbol, expiration)

    # Get the most recent quote
    quote = get_quote(config_file, symbol)
    stock_price = quote.get_price()

    days = 0
    count = 0

    for strike_price in option_chain.get_strike_prices():
        if days == 0:
            # Calculate the number of days until expiration
            time_delta = option_chain.get_expiration().date() - datetime.date.today()
            days = time_delta.days

        call = option_chain.get_call_option(strike_price)

        open_interest = call.get_open_interest()
        call_premium = call.get_bid()

        intrinsic_value = 0.0
        stock_upside = 0.0
        time_value = call_premium

        if strike_price < stock_price:
            # In the money
            intrinsic_value = stock_price - strike_price
            time_value = call_premium - intrinsic_value
            stock_upside = 0.0
        else:
            intrinsic_value = 0.0
            time_value = call_premium
            stock_upside = strike_price - stock_price

        roo = time_value / strike_price
        upside = stock_upside / stock_price
        total_gain = roo + upside

        total_profit = time_value + stock_upside 

        roo_annual = (365/days) * roo
        upside_annual = (365/days) * upside
        total_annual = roo_annual + upside_annual

        downside_protection = intrinsic_value / stock_price
        delta = call.get_delta()

        min_open_interest = tone_config.get("min_open_interest",DEFAULT_MIN_OPEN_INTEREST)
        min_annual_roo = tone_config.get("min_annual_roo", DEFAULT_MIN_ANNUAL_ROO)
        max_annual_roo = tone_config.get("max_annual_roo", DEFAULT_MAX_ANNUAL_ROO)
        min_annual_upside = tone_config.get("min_annual_upside", DEFAULT_MIN_ANNUAL_UPSIDE)
        min_downside = tone_config.get("min_downside", DEFAULT_MIN_DOWNSIDE)
        min_delta = tone_config.get("min_delta", DEFAULT_MIN_DELTA)
        max_delta = tone_config.get("max_delta", DEFAULT_MAX_DELTA)

        if open_interest < min_open_interest:
            if debug:
                print(f"{call.get_display_symbol()} open_interest {open_interest} is too low min={min_open_interest}")
            continue

        if downside_protection < min_downside:
            # Not enough downside protection
            if debug:
                print(f"{call.get_display_symbol()} downside_protection {downside_protection:.2f} is too low min={min_downside}")
            continue

        if roo_annual < min_annual_roo:
            # Not enough option profit potential
            if debug:
                print(f"{call.get_display_symbol()} roo_annual {roo_annual:.2f} is too low min={min_annual_roo}")
            continue

        if delta < min_delta:
            # delta is too low
            if debug:
                print(f"{call.get_display_symbol()} delta {delta} is too low min={min_delta}")
            continue

        if delta > tone_config.get("max_delta", DEFAULT_MAX_DELTA):
            if debug:
                print(f"{call.get_display_symbol()} delta {delta} is too high max={max_delta}")
            # delta is too high
            continue

        if roo_annual > max_annual_roo:
            # Too risky on the option
            if debug:
                print(f"{call.get_display_symbol()} roo_annual {roo_annual:.2f} is too high max={max_annual_roo}")
            continue

        if upside_annual < min_annual_upside:
            # Not enough upside profit potential
            if debug:
                print(f"{call.get_display_symbol()} upside_annual {upside_annual:.2f} is too low min={min_annual_upside}")
            continue

        count += 1

        if verbose:
            print(f"{call.get_display_symbol()}: price={stock_price} days={days} premium=${call_premium:.2f}")
            print(f"\tProtection: {100*downside_protection:6.2f}%\t\tDelta : {delta:8.4f}")
            print(f"\tROO       : {100*roo:6.2f}% ({100*roo_annual:6.2f}%)\tProfit: ${100*time_value:7.2f}")
            print(f"\tUpside    : {100*upside:6.2f}% ({100*upside_annual:6.2f})%\tProfit: ${100*stock_upside:7.2f}")
            print(f"\tTotal     : {100*total_gain:6.2f}% ({100*total_annual:6.2f}%)\tTotal : ${100*total_profit:7.2f}")
            print()
        else:
            print(f"{call.get_display_symbol()}: price={stock_price} days={days} roo={100*roo:.2f}%({100*roo_annual:0.2f}%) downside={100*downside_protection:.2f}% upside={100*upside:.2f}%({100*upside_annual:.2f}%) total={100*total_gain:.2f}%({100*total_annual:.2f}%)")

    if count == 0:
        print("No matching options found")

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-e','--expiration', dest='expiration', required=False,default=None,help="Expiration Date <YYYY-MM-DD>" )
    parser.add_argument('-d','--debug', dest='debug', required=False,default=False,action='store_true',help="Expiration Date <YYYY-MM-DD>" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-m','--market-tone', dest='market_tone', required=True,help="Market tone configuration" )

    expiration = None
    args = parser.parse_args()

    if args.expiration is not None:
        (y,m,d) = args.expiration.split("-")
        expiration = datetime.datetime(year=int(y),month=int(m), day=int(d))

    main(args.config_file,args.market_tone,args.symbol,expiration,args.debug,args.verbose)

