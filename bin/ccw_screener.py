#! /usr/bin/python3

import argparse
import datetime
import sys
from etrade_tools import *

DEFAULT_CONFIG_FILE="etrade.json"
DEFAULT_SCREENER_CONFIG="stock_screener.json"
DEFAULT_TONE_FILE="tone/market-neutral.json"

DEFAULT_MIN_OPEN_INTEREST=25
DEFAULT_MIN_ANNUAL_ROO=0.0
DEFAULT_MAX_ANNUAL_ROO=2.0
DEFAULT_MIN_ANNUAL_UPSIDE=0.0

DEFAULT_MIN_DOWNSIDE=0.0
DEFAULT_MIN_DELTA=0.0
DEFAULT_MAX_DELTA=1.0

PCR_VALUE_OVERSOLD=1.3
PCR_VALUE_OVERBOUGHT=0.5

PCR_STRING_NORMAL="normal"
PCR_STRING_OVERSOLD="over sold"
PCR_STRING_OVERBOUGHT="over bought"

global GLOBAL_DEBUG
global GLOBAL_VERBOSE

def main(config_file,screener_config_file,market_tone_config,symbol_list,expiration,output_file):
    count = 0
    fh = None
    screener_config = read_json_file(screener_config_file)
    if output_file:
        try:
            fh = open(output_file,"w")
            fh.write("Symbol,Company Name,Sector,Score,Option,Days,Price,Premium,Mark,Total Cost,Open Interest,Beta,Put/Call Ratio,Max Pain,Downside Protection(%),Delta,Return On Option(%),ROO Annualized(%),Profit($),Upside Potential(%),Upside Annualize(%),Upside Profit($),Total Gain(%),Total Annualized(%),Total Profit($)" + "\n")
        except (PermissionError, IOError) as e:
            print(f"Error: could not open {output_file} for writing: {e}")
            sys.exit(1)
    for symbol in symbol_list:
        count += 1
        option_list = find_covered_calls(config_file,screener_config_file,market_tone_config,symbol,expiration)

        for cco in option_list:
            if GLOBAL_VERBOSE:
                print(f"{cco.get('display_symbol')}: days={cco.get('days')} price={cco.get('stock_price')} premium=${cco.get('premium'):.2f}(mark={cco.get('mark'):.2f}) cost=${cco.get('total_cost'):.2f}")
                print(f"\tDetails   : oi={cco.get('oi')} beta={cco.get('beta'):.2f} pcr={cco.get('pcr'):.2f}({cco.get('pcr_string')}) max pain=${cco.get('max_pain'):.2f}")
                print(f"\tProtection: {cco.get('downside'):6.2f}%\t\tDelta : {cco.get('delta'):8.4f}")
                print(f"\tROO       : {cco.get('roo'):6.2f}% ({cco.get('roo_annual'):6.2f}%)\tProfit: ${cco.get('profit'):7.2f}")
                print(f"\tUpside    : {cco.get('upside'):6.2f}% ({cco.get('upside_annual'):6.2f}%)\tProfit: ${cco.get('upside_profit'):7.2f}")
                print(f"\tTotal     : {cco.get('total_gain'):6.2f}% ({cco.get('total_annual'):6.2f}%)\tTotal : ${cco.get('total_profit'):7.2f}")
                print()
            else:
                print(f"{cco.get('display_symbol')}: price={cco.get('stock_price')} days={cco.get('days')} roo={cco.get('roo'):.2f}%({cco.get('roo_annual'):0.2f}%) downside={cco.get('downside'):.2f}% upside={cco.get('upside'):.2f}%({cco.get('upside_annual'):5.2f}%) total={cco.get('total_gain'):.2f}%({cco.get('total_annual'):.2f}%)")

            if output_file:
                fh.write(f"{symbol.upper()}," + 
                    '"' + f"{cco.get('company_name')}" + '",' +
                    '"' + f"{cco.get('sector')}" + '",' +
                    f"{get_score(screener_config,symbol)},"+
                    '"' + f"{cco.get('display_symbol')}" +'",' +
                    f"{cco.get('days')},"+
                    f"{cco.get('stock_price'):.2f}," +
                    f"{cco.get('premium'):.2f}," +
                    f"{cco.get('mark'):.2f}," +
                    f"{cco.get('total_cost'):.2f}," +
                    f"{cco.get('oi')}," +
                    f"{cco.get('beta')}," +
                    f"{cco.get('pcr'):.2f}," +
                    f"{cco.get('max_pain'):.2f}," +
                    f"{cco.get('downside'):.2f}," +
                    f"{cco.get('delta'):.4f}," +
                    f"{cco.get('roo'):.2f}," +
                    f"{cco.get('roo_annual'):.2f}," +
                    f"{cco.get('profit'):.2f}," +
                    f"{cco.get('upside'):.2f}," +
                    f"{cco.get('upside_annual'):.2f}," +
                    f"{cco.get('upside_profit'):.2f}," +
                    f"{cco.get('total_gain'):.2f}," +
                    f"{cco.get('total_annual'):.2f}," +
                    f"{cco.get('total_profit'):.2f}" + "\n"
                    )
                fh.flush()
            

    if output_file:
        fh.close()

    if count == 0:
        print("No symbols found")

def find_covered_calls(config_file,screener_config_file,market_tone_config,symbol,expiration):
    option_list = list()
    # Get the market tone config
    tone_config = read_json_file(market_tone_config)

    # Get the option chain
    try:
        option_chain = get_option_chain(config_file, symbol, expiration)
    except OptionChainNotFoundError as e:
        print(f"{symbol} No option chain found for {expiration}")
        return option_list

    # Get the most recent quote
    screener_config = read_json_file(screener_config_file)
    quote = get_quote(config_file, symbol,screener_config)
    stock_price = quote.get_price()
    beta = quote.get_beta()

    pcr = option_chain.get_put_call_ratio()
    pcr_string = PCR_STRING_NORMAL
    if pcr >= PCR_VALUE_OVERSOLD:
        pcr_string = PCR_STRING_OVERSOLD
    elif pcr <= PCR_VALUE_OVERBOUGHT:
        pcr_string = PCR_STRING_OVERBOUGHT

    days = 0
    count = 0

    for strike_price in option_chain.get_strike_prices():
        if days == 0:
            # Calculate the number of days until expiration
            time_delta = option_chain.get_expiration().date() - datetime.date.today()
            days = time_delta.days

        call = option_chain.get_call_option(strike_price)

        if call.get_adjusted_flag is False:
            debug(f"{call.get_display_symbol()} is an adjusted option, skipping")
            continue

        open_interest = call.get_open_interest()
        call_premium = call.get_bid()
        ask_premium = call.get_ask()
        max_pain = option_chain.get_max_pain()
        mark = float((call_premium + ask_premium)/2)

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

        total_cost = 100 * (stock_price - call_premium)

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
            debug(f"{call.get_display_symbol()} open_interest {open_interest} is too low min={min_open_interest}")
            continue

        if downside_protection < min_downside:
            # Not enough downside protection
            debug(f"{call.get_display_symbol()} downside_protection {downside_protection:.2f} is too low min={min_downside}")
            continue

        if roo_annual < min_annual_roo:
            # Not enough option profit potential
            debug(f"{call.get_display_symbol()} roo_annual {roo_annual:.2f} is too low min={min_annual_roo}")
            continue

        if delta > 0 and delta < min_delta:
            # delta is too low
            debug(f"{call.get_display_symbol()} delta {delta} is too low min={min_delta}")
            continue

        if delta > tone_config.get("max_delta", DEFAULT_MAX_DELTA):
            # delta is too high
            debug(f"{call.get_display_symbol()} delta {delta} is too high max={max_delta}")
            continue

        if roo_annual > max_annual_roo:
            # Too risky on the option
            debug(f"{call.get_display_symbol()} roo_annual {roo_annual:.2f} is too high max={max_annual_roo}")
            continue

        if upside_annual < min_annual_upside:
            # Not enough upside profit potential
            debug(f"{call.get_display_symbol()} upside_annual {upside_annual:.2f} is too low min={min_annual_upside}")
            continue

        count += 1

        matching_call = {
            "display_symbol": call.get_display_symbol(),
            "days" : days,
            "stock_price" : stock_price,
            "premium" : call_premium,
            "mark" : mark,
            "total_cost" : total_cost,
            "oi" : open_interest,
            "beta" : beta,
            "pcr" : pcr,
            "pcr_string" : pcr_string,
            "max_pain" : max_pain,
            "roo" : roo * 100,
            "roo_annual" : roo_annual * 100,
            "downside" : downside_protection * 100,
            "delta" : delta,
            "profit" : time_value * 100,
            "upside" : upside * 100,
            "upside_annual" : upside_annual * 100,
            "upside_profit" : stock_upside * 100,
            "total_gain" : total_gain * 100,
            "total_annual" : total_annual * 100,
            "total_profit" : total_profit * 100,
            "sector" : quote.get_sector(),
            "company_name" : quote.get_company_name()
        }

        option_list.append(matching_call)

    if count == 0:
        print(f"{symbol} No matching options found")

    return option_list

def debug(msg):
    if GLOBAL_DEBUG:
        print(msg)

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

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', help="Symbol to search (conflicts with -r)" )
    parser.add_argument('-r','--results-file', dest='results', help="Results CSV file to use as input (conflicts with -s)" )
    parser.add_argument('-o','--output-csv', dest='output', help="CSV file to write the output to")
    parser.add_argument('-e','--expiration', dest='expiration', required=False,default=None,help="Expiration Date <YYYY-MM-DD>" )
    parser.add_argument('-d','--debug', dest='debug', required=False,default=False,action='store_true',help="Enable debugging" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-m','--market-tone', dest='market_tone',default=DEFAULT_TONE_FILE,help="Market tone configuration" )

    expiration = None
    args = parser.parse_args()

    if args.expiration is not None:
        (y,m,d) = args.expiration.split("-")
        expiration = datetime.datetime(year=int(y),month=int(m), day=int(d))

    GLOBAL_DEBUG = args.debug
    GLOBAL_VERBOSE = args.verbose

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
    main(args.config_file,screener_config_file,args.market_tone,symbol_list,expiration,args.output)

