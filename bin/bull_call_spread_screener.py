#! /usr/bin/python3

import argparse
import datetime
import sys
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"
DEFAULT_SCREENER_CONFIG="./etc/stock_screener.json"
DEFAULT_PARAMS_FILE="./etc/bull_call_spread.json"

DEFAULT_MIN_OPEN_INTEREST=25
DEFAULT_MIN_ANNUAL_ROO=0.4
DEFAULT_MIN_DOWNSIDE=0.05
DEFAULT_MIN_SHORT_DELTA=0.0
DEFAULT_MIN_LONG_DELTA=1.0

global GLOBAL_DEBUG
global GLOBAL_VERBOSE

def main(config_file,screener_config_file,option_parameters_file,symbol_list,expiration,output_file):
    count = 0
    fh = None
    screener_config = read_json_file(screener_config_file)
    option_parameters = read_json_file(option_parameters_file)
    if output_file:
        try:
            fh = open(output_file,"w")
            fh.write("Symbol,Company Name,Sector,Score,Price,Days,Long Call Strike,Long Call Ask,Long Call Time Value,Long Call IO,Long Call Delta,Short Call Strike,Short Call Bid,Short Call Premium,Short Call IO,Short Call Delta,Break Event,Total Cost,Profit,ROO,ROO Annualized,Downside Protection" + "\n")
        except (PermissionError, IOError) as e:
            print(f"Error: could not open {output_file} for writing: {e}")
            sys.exit(1)
    for symbol in symbol_list:
        count += 1
        option_list = get_bull_call_spreads(config_file,screener_config,option_parameters,symbol,expiration)
        for bcs in option_list:
            if output_file:
                fh.write(f"{symbol.upper()}," + 
                    '"' + f"{bcs.get('company_name')}" + '",' +
                    '"' + f"{bcs.get('sector')}" + '",' +
                    f"{get_score(screener_config,symbol)},"+
                    f"{bcs.get('stock_price'):.2f}," +
                    f"{bcs.get('days')},"+
                    f"{bcs.get('long_call_strike'):.2f}," +
                    f"{bcs.get('long_call_ask'):.2f}," +
                    f"{bcs.get('long_call_time_value'):.2f}," +
                    f"{bcs.get('long_call_oi')}," +
                    f"{bcs.get('long_call_delta'):.4f}," +
                    f"{bcs.get('short_call_strike'):.2f}," +
                    f"{bcs.get('short_call_bid'):.2f}," +
                    f"{bcs.get('short_call_time_value'):.2f}," +
                    f"{bcs.get('short_call_oi')}," +
                    f"{bcs.get('short_call_delta'):.4f}," +
                    f"{bcs.get('break_even'):.2f}," +
                    f"{bcs.get('cost'):.2f}," +
                    f"{bcs.get('profit'):.2f}," +
                    f"{bcs.get('roo'):.2f}," +
                    f"{bcs.get('roo_annual'):.2f}," +
                    f"{bcs.get('downside'):.2f}" +
                    "\n"
                    )

    if output_file:
        fh.close()

    if count == 0:
        print("No symbols found")

def get_bull_call_spreads(config_file,screener_config,option_parameters,symbol,expiration):
    # Get the option chain
    call_spread_list = list()
    try:
        option_chain = get_option_chain(config_file, symbol, expiration)
    except OptionChainNotFoundError as e:
        print(f"{symbol} No option chain found for {expiration}")
        return call_spread_list

    # Get the most recent quote
    quote = get_quote(config_file, symbol, screener_config)

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

            matching_call_spread = {
                "days" : days,
                "long_call_strike"       : long_call_strike_price,
                "long_call_ask"          : long_call_ask,
                "long_call_time_value"   : long_call_theta,
                "long_call_oi"           : long_call.get_open_interest(),
                "long_call_delta"        : long_call.get_delta(),
                "short_call_strike"      : short_call_strike_price,
                "short_call_bid"         : short_call_bid,
                "short_call_time_value"  : short_call_theta,
                "short_call_oi"          : short_call.get_open_interest(),
                "short_call_delta"       : short_call.get_delta(),
                "break_even"             : short_call_strike_price - theta_spread,
                "cost"                   : cost,
                "profit"                 : 100 * theta_spread,
                "roo"                    : 100 * return_on_spread,
                "roo_annual"             : 100 * roo_annualized,
                "downside"               : 100 * downside_protection,
                "sector"                 : quote.get_sector(),
                "company_name"           : quote.get_company_name(),
                "stock_price"            : quote.get_price()
                }
            call_spread_list.append(matching_call_spread)

    if count == 0:
        print(f"{symbol}: No matching bull call spreads found")

    return call_spread_list

def get_symbols_from_results_file(results_file):
    symbols = list()
    try:
        with open(results_file,"r") as f:
            for line in f.readlines():
                if line.startswith("Symbol"):
                    continue
                symbol = line.split(",")[0]
                symbols.append(symbol)
                
    except IOError as e:
        print(f"Error reading '{results_file}': {e}")
        sys.exit(1)
    return symbols

def debug(msg):
    if GLOBAL_DEBUG:
        print(msg)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', help="Symbol to search (conflicts with -r)" )
    parser.add_argument('-r','--results-file', dest='results', help="Results CSV file to use as input (conflicts with -s)" )
    parser.add_argument('-o','--output-csv', dest='output', help="CSV file to write the output to")
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

    if args.symbol and args.results:
        print("Error: --symbol (-s) and --results-file (-r) conflict with each other")
        sys.exit(1)

    symbol_list = list()
    if args.symbol:
        symbol_list.append(args.symbol)
    elif args.results:
        if not args.output:
            print("Error: --results-file (-r) requires --output-csv (-o)")
            sys.exit(1)
        if os.path.exists(args.output):
            print(f"Error: output csv {args.output} already exists, exiting")
            sys.exit(1)
        
        symbol_list = get_symbols_from_results_file(args.results)
    else:
        print("Error: must specify either --symbol (-s) or --results-file (-r)")
        sys.exit(1)

    screener_config_file = DEFAULT_SCREENER_CONFIG
    main(args.config_file,screener_config_file,args.parameters,symbol_list,expiration,args.output)

