#! /usr/bin/python3

import argparse
import datetime
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"
DEFAULT_PARAMS_FILE="bull_call_spread.json"

DEFAULT_MIN_OPEN_INTEREST=25
DEFAULT_MIN_ANNUAL_ROO=0.4
DEFAULT_MIN_DOWNSIDE=0.05
DEFAULT_MIN_SHORT_DELTA=0.0
DEFAULT_MIN_LONG_DELTA=1.0

global GLOBAL_DEBUG
global GLOBAL_VERBOSE

def main(config_file,option_parameters_file,symbol,expiration):
    # Get the market tone config
    option_parameters = read_json_file(option_parameters_file)

    # Get the option chain
    try:
        option_chain = get_option_chain(config_file, symbol, expiration)
    except OptionChainNotFoundError as e:
        print(f"{symbol} No option chain found for {expiration}")
        return

    # Get the most recent quote
    quote = get_quote(config_file, symbol)

    price = quote.get_price()

    min_open_interest = option_parameters.get("min_open_interest",DEFAULT_MIN_OPEN_INTEREST)
    min_annual_roo = option_parameters.get("min_annual_roo", DEFAULT_MIN_ANNUAL_ROO)
    min_downside = option_parameters.get("min_downside", DEFAULT_MIN_DOWNSIDE)
    min_short_call_delta = option_parameters.get("min_short_delta", DEFAULT_MIN_SHORT_DELTA)
    min_long_call_delta = option_parameters.get("min_long_delta", DEFAULT_MIN_LONG_DELTA)
    
    days = 0
    count = 0
    for long_call_strike_price in option_chain.get_strike_prices():
        long_call = option_chain.get_call_option(long_call_strike_price)

        if long_call.get_adjusted_flag is False:
            debug(f"LC: {symbol}/{long_call_strike_price} is an adjusted option")
            continue
            
        if days == 0:
            # Calculate the number of days until expiration
            time_delta = option_chain.get_expiration().date() - datetime.date.today()
            days = time_delta.days

        # Filter on long call open interest
        if long_call.get_open_interest() < min_open_interest:
            debug(f"LC: {symbol}/{long_call_strike_price}: long call open interest too low {long_call.get_open_interest()} < {min_open_interest}")
            continue
            
        if long_call.get_delta() < min_long_call_delta:
            debug(f"LC: {symbol}/{long_call_strike_price}: long call delta too low {long_call.get_delta():.2f} < {min_long_call_delta}")
            break

        for short_call_strike_price in option_chain.get_strike_prices():
            short_call = option_chain.get_call_option(short_call_strike_price)

            if short_call_strike_price <= long_call_strike_price:
                continue

            if short_call.get_adjusted_flag is False:
                debug(f"SC: {symbol}/{short_call_strike_price} is an adjusted option")
                continue
                
            # Filter on long call open interest
            if short_call.get_open_interest() < min_open_interest:
                debug(f"SC: {symbol}/{short_call_strike_price}: short call open interest too low {short_call.get_open_interest()} < {min_open_interest}")
                continue
                
            if short_call.get_delta() < min_short_call_delta:
                debug(f"SC: {symbol}/{short_call_strike_price}: short call delta too low {short_call.get_delta():.2f} < {min_short_call_delta}")
                break

            long_call_ask = long_call.get_ask()
            long_call_theta = long_call_ask - (price - long_call_strike_price)

            short_call_bid = short_call.get_bid()
            short_call_theta = short_call_bid - (price - short_call_strike_price)

            downside_protection = 1 - (short_call_strike_price / price)
            if downside_protection < min_downside:
                debug(f"LC({long_call_strike_price})/SC({short_call_strike_price}) downside protection {downside_protection:.2f} < {min_downside}")
                continue

            theta_spread = short_call_theta - long_call_theta

            if theta_spread < 0:
                debug(f"LC({long_call_strike_price})/SC({short_call_strike_price}) theta spread {theta_spread:.2f} < 0")
                continue

            cost = 100 * (long_call_ask - short_call_bid)

            return_on_spread = (100 * theta_spread) / cost
            roo_annualized = (365/days) * return_on_spread

            if roo_annualized < min_annual_roo:
                debug(f"LC({long_call_strike_price})/SC({short_call_strike_price}) annualize roo {roo_annualized:.2f} < {min_annual_roo}")
                continue

            count += 1
            if GLOBAL_VERBOSE:
                print(f"{symbol.upper()}({option_chain.get_expiration().date()}) Bull Credit Spread: days={days}  price=${price:.2f}  beta={quote.get_beta():.2f}")
                print(f"\tLong Call : ${long_call_strike_price:6.2f}  ask=${long_call_ask:.2f}  time value=${long_call_theta:.2f}  oi={long_call.get_open_interest()}  delta={long_call.get_delta()}")
                print(f"\tShort Call: ${short_call_strike_price:6.2f}  bid=${short_call_bid:.2f}  time value=${short_call_theta:.2f}  oi={short_call.get_open_interest()}  delta={short_call.get_delta()}")
                print(f"\tBreak even: ${short_call_strike_price - theta_spread:9.2f}")
                print(f"\tCost      : ${cost:9.2f}")
                print(f"\tProfit    : ${100*theta_spread:9.2f}")
                print(f"\tROO       : {100*return_on_spread:10.2f}% ({100*roo_annualized:6.2f}%)")
                print(f"\tProtection: {100*downside_protection:10.2f}%")
                print()
            else:
                print(f"{symbol} long call: {long_call_strike_price} short call : {short_call_strike_price}: downside protection {100 * downside_protection:.2f}% annualized roo {100 * roo_annualized:.2f}%")

    if count == 0:
        print(f"{symbol}: No matching bull call spreads found")

def debug(msg):
    if GLOBAL_DEBUG:
        print(msg)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol to search" )
    parser.add_argument('-e','--expiration', dest='expiration', required=False,default=None,help="Expiration Date <YYYY-MM-DD>" )
    parser.add_argument('-d','--debug', dest='debug_flag', required=False,default=False,action='store_true',help="Enable debugging" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-p','--paramaters', dest='parameters',default=DEFAULT_PARAMS_FILE,help="Option parameters configuration" )

    expiration = None
    args = parser.parse_args()

    if args.expiration is not None:
        (y,m,d) = args.expiration.split("-")
        expiration = datetime.datetime(year=int(y),month=int(m), day=int(d))

    GLOBAL_VERBOSE = args.verbose
    GLOBAL_DEBUG = args.debug_flag

    main(args.config_file,args.parameters,args.symbol,expiration)

