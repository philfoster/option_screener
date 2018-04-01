#! /usr/bin/python

from options_tools import *
import argparse
import logging

# Setup the defaults
DEFAULT_SYMBOL_FILE = "symbols.txt"
DEFAULT_MIN_YIELD = 1.0
DEFAULT_MAX_PE_RATIO = 30
DEFAULT_MIN_DAYS = 23
DEFAULT_MAX_DAYS = 75
DEFAULT_MAX_PRICE = 400
DEFAULT_MIN_OPEN_INTEREST = 10
DEFAULT_MAX_ASK = 5
DEFAULT_MIN_ASK = .05
DEFAULT_BREAK_EVEN_PERCENT = 2
DEFAULT_MIN_TARGET_PRICE_PERCENT = 30
DEFAULT_TARGET_PRICE_PERCENT = 3
DEFAULT_COMMISSION_COST = 7.73

# Other defaults
OUTPUT_BASENAME = "./call_options"

def main():

    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', dest='filename', help="File containing symbol list", default=DEFAULT_SYMBOL_FILE)
    parser.add_argument('--symbol', dest='symbol', help="Symbol to search" )
    parser.add_argument('--commission', dest='commission_cost', help="Commission cost", default=DEFAULT_COMMISSION_COST )
    parser.add_argument('--max_price', dest='max_price', type=float, help="Maximum share price", default=DEFAULT_MAX_PRICE)
    parser.add_argument('--yield', dest='min_yield', type=float, help="Minumum yield", default=DEFAULT_MIN_YIELD)
    parser.add_argument('--pe_ratio', dest='max_pe_ratio', type=float, help="Maximum P/E Ratio", default=DEFAULT_MAX_PE_RATIO)
    parser.add_argument('--open_interest', dest='min_open_interest', type=float, help="Minumum open interest", default=DEFAULT_MIN_OPEN_INTEREST)
    parser.add_argument('--min_days', dest='min_days', type=float, help="Minimum days remaining", default=DEFAULT_MIN_DAYS)
    parser.add_argument('--max_days', dest='max_days', type=float, help="Maximum days remaining", default=DEFAULT_MAX_DAYS)
    parser.add_argument('--min_ask', dest='min_ask', type=float, help="Minumum ask price", default=DEFAULT_MIN_ASK)
    parser.add_argument('--max_ask', dest='max_ask', type=float, help="Maximum ask price", default=DEFAULT_MAX_ASK)
    parser.add_argument('--break_even', dest='break_even_percent', type=float, help="Maximum break even percentage", default=DEFAULT_BREAK_EVEN_PERCENT)
    parser.add_argument('--target_percent', dest='target_price_percent', type=float, help="Target price gain percent", default=DEFAULT_TARGET_PRICE_PERCENT)
    parser.add_argument('--min_price_target', dest='min_target_price_percent', type=float, help="Minimum price target percentage on target price gain", default=DEFAULT_MIN_TARGET_PRICE_PERCENT)

    # Process the args
    args = parser.parse_args()
    symbol_file = args.filename

    symbol_list = list()

    if args.symbol:
        symbol_list.append ( args.symbol )
    else:
        symbol_list = get_symbols ( symbol_file )
        
    logging.basicConfig ( filename="screener.log", level=logging.DEBUG, format='%(asctime)s %(message)s')

    viable_calls = get_safe_calls ( symbol_list, args )

    if not viable_calls:
        logging.info( "No viable calls detected" )
        print "No viable calls detected"
        exit ( 0 )

    output_csv = "{0}.{1}.csv".format ( OUTPUT_BASENAME, time.strftime('%Y-%m-%d-%H-%M',  time.localtime()) )
    if args.symbol:
        output_csv = "{0}.{1}.{2}.csv".format ( OUTPUT_BASENAME, args.symbol, time.strftime('%Y-%m-%d-%H-%M',  time.localtime()) )

    f = file ( output_csv, "w" )
    f.write ( "Symbol,Price,P/E Ratio,Yield,Ex-Dividend Date,Expiration Date,Strike Price,Ask,Break Even,Cost,Price at +{0}%,Proceeds at +{0}%,Gain$ at +{0}%, Gain% at +{0}%\n".format ( args.target_price_percent ) )

    # Setup factors
    target_price_factor = 1 + ( args.target_price_percent / 100.0 )

    logging.info ( "Writing results to {0}".format(output_csv) )
    print "Writing results to {0}".format(output_csv)
    for call in viable_calls:
        (symbol,price,pe_ratio,div_yield,div_date,exp_date,strike,ask) = call

        price_at_target = float(price) * target_price_factor
        gain_at_target = price_at_target - strike
        proceeds_at_target = ( gain_at_target * 100 ) - args.commission_cost

        cost_to_buy = ( ask * 100 ) + args.commission_cost

        profit_dollars = proceeds_at_target - cost_to_buy
        profit_percent = ( profit_dollars / cost_to_buy )

        f.write("{0},{1},{2},{3},\"{4}\",{5},{6},{7},{8},{9},{10},{11},{12},{13:.2%}\n".format ( symbol, price, pe_ratio, div_yield,div_date,exp_date,strike,ask,(strike + ask),cost_to_buy,price_at_target,proceeds_at_target,profit_dollars,profit_percent) )

    f.close()

if __name__ == '__main__':
    main()
