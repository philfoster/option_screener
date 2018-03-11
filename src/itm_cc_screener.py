#! /usr/bin/python

from options_tools import *
import argparse
import logging

# Setup the defaults
DEFAULT_SYMBOL_FILE = "symbols.txt"
DEFAULT_MIN_YIELD = 1.0
DEFAULT_MAX_PE_RATIO = 50
DEFAULT_MIN_DAYS = 14
DEFAULT_MAX_DAYS = 48
DEFAULT_MIN_PRICE = 30
DEFAULT_MAX_PRICE = 75
DEFAULT_MAX_ASK = 100
DEFAULT_MIN_ASK = .02
DEFAULT_MIN_OPEN_INTEREST = 5
DEFAULT_COMMISSION_COST = 4.95 + 0.5
DEFAULT_MIN_TARGET_PRICE_PERCENT = 30
DEFAULT_TARGET_PRICE_PERCENT = 3

# Other defaults
OUTPUT_BASENAME = "./call_options"

def main():

    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', dest='filename', help="File containing symbol list", default=DEFAULT_SYMBOL_FILE)
    parser.add_argument('--symbol', dest='symbol', help="Symbol to search" )
    parser.add_argument('--commission', dest='commission_cost', help="Commission cost", default=DEFAULT_COMMISSION_COST )
    parser.add_argument('--min_price', dest='min_price', type=float, help="Minimum share price", default=DEFAULT_MIN_PRICE)
    parser.add_argument('--max_price', dest='max_price', type=float, help="Maximum share price", default=DEFAULT_MAX_PRICE)
    parser.add_argument('--yield', dest='min_yield', type=float, help="Minumum yield", default=DEFAULT_MIN_YIELD)
    parser.add_argument('--pe_ratio', dest='max_pe_ratio', type=float, help="Maximum P/E Ratio", default=DEFAULT_MAX_PE_RATIO)
    parser.add_argument('--open_interest', dest='min_open_interest', type=float, help="Minumum open interest", default=DEFAULT_MIN_OPEN_INTEREST)
    parser.add_argument('--min_days', dest='min_days', type=float, help="Minimum days remaining", default=DEFAULT_MIN_DAYS)
    parser.add_argument('--max_days', dest='max_days', type=float, help="Maximum days remaining", default=DEFAULT_MAX_DAYS)
    parser.add_argument('--min_ask', dest='min_ask', type=float, help="Minumum ask price", default=DEFAULT_MIN_ASK)
    parser.add_argument('--max_ask', dest='max_ask', type=float, help="Maximum ask price", default=DEFAULT_MAX_ASK)
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
        
    logging.basicConfig ( filename="itm_cc_screener.log", level=logging.DEBUG, format='%(asctime)s %(message)s')

    itm_calls = get_itm_covered_calls ( symbol_list, args )

    if not itm_calls:
        logging.info( "No itm calls detected" )
        print "No itm calls detected"
        exit ( 0 )

    print "Symbol,Price,P/E Ratio,Dividend Yield,Ex-Dividend Date,Expiration Date,Strike,Bid,Max gain$,Max gain%,Cost basis,Loss %,Out of Pocket cost"
    for itm_call in itm_calls:
        (symbol,price, pe_ratio,div_yield,ex_date,date_key,strike,bid,ask) = itm_call
        intrinsic_value = float(price - strike)

        # time_value is the maximum gain possible
        time_value = float(bid - intrinsic_value)

        # End up paying two commissions on this:
        # 1. buying the stock
        # 2. selling the call
        out_of_pocket = ( 100 * ( price - bid ) ) + ( args.commission_cost * 2 )

        max_gain = float ( 100 * time_value ) - (args.commission_cost * 2 )
        max_gain_percentage = max_gain / out_of_pocket

        # Now calculate the loss it would take to lose money
        cost_basis = out_of_pocket / 100

        loss = price - cost_basis
        loss_percentage = loss / price

        if max_gain < 0:
            logging.info ( "Skipping {0} {1} {2} call, there is no possible gain (price={3},bid={4})".format ( symbol, date_key, strike, price, bid ) )
            continue

        if max_gain_percentage < 0.01:
            logging.info ( "Skipping {0} {1} {2} call, max gain is less than 1% ({3:.2%})".format ( symbol, date_key, strike, max_gain_percentage ) )
            continue

        if loss_percentage < 0.05:
            logging.info ( "Skipping {0} {1} {2} call, too risky (less than 5% cushion) ({3:.2%})".format ( symbol, date_key, strike, loss_percentage ) )
            continue

        print "{0},{1},{2},{3},\"{4}\",\"{5}\",{6},{7},{8},{9:.2%},{10},{11:.2%},{12}".format ( symbol, price, pe_ratio, div_yield, ex_date, date_key, strike, bid, max_gain, max_gain_percentage, cost_basis, loss_percentage, out_of_pocket  )
        

def get_itm_covered_calls ( symbols, args ):
    itm_calls = set()

    for symbol in symbols:
        logging.info ( "Looking for options on {0}".format ( symbol ) )
        print "Looking for options on {0}".format ( symbol )
        # Details data
        data = get_details ( symbol )

        # Check the price
        if float(data["price"]) > args.max_price:
            print "Skipping {0}, price is too high {1}".format ( symbol, data["price"] )
            logging.info ( "Skipping {0}, price is too high {1}".format ( symbol, data["price"] ) )
            continue

        if float(data["price"]) < args.min_price:
            print "Skipping {0}, price is too low {1}".format ( symbol, data["price"] )
            logging.info ( "Skipping {0}, price is too low {1}".format ( symbol, data["price"] ) )
            continue

        # Check the p/e ratio
        if float(data["P/E Ratio"]) > args.max_pe_ratio:
            print "Skipping {0}, P/E Ratio is too high {1}".format ( symbol, data["P/E Ratio"] )
            logging.info ( "Skipping {0}, P/E Ratio is too high {1}".format ( symbol, data["P/E Ratio"] ) )
            continue

        # Check the yield
        yield_match = re.search ( '^([\d\.]+)\%?', data["Yield"] )
        if yield_match:
            div_yield = yield_match.group(1)
            if float(div_yield) < args.min_yield:
                print "Skipping {0}, yield is too low {1}".format ( symbol, data["Yield"] )
                logging.info ( "Skipping {0}, yield is too low {1}".format ( symbol, data["Yield"] ) )
                continue
        else:
            logging.info ( "Skipping {0}, yield is too low {1}".format ( symbol, data["Yield"] ) )
            continue

        # Option chain
        data["call_options"] = get_itm_call_options ( symbol, float(data["price"]), args )
        logging.debug ( data )
        
        for date_key in data["call_options"]:
            for call_id in data["call_options"][date_key]:
                bid = data["call_options"][date_key][call_id]["bid"]
                ask = data["call_options"][date_key][call_id]["ask"]
                strike = data["call_options"][date_key][call_id]["strikePrice"]

                if strike <= float(data["price"]):
                    print "ITM option: {0} {1} {2} call bid {3}, ask {4}".format( symbol, date_key, strike, bid, ask )
                    logging.info ( "In the money option: {0} {1} {2} call bid {3}, ask {4}".format( symbol, date_key, strike, bid, ask ) )

                    good_call = (symbol,float(data["price"]),data["P/E Ratio"],data["Yield"],data["Ex-Dividend Date"],date_key,float(strike),float(bid),float(ask))
                    itm_calls.add ( good_call )
                else:
                    logging.info ( "Skipping {0}, it's out of the money price={1}".format ( strike, data["price"] ) )

    return itm_calls

    

if __name__ == '__main__':
    main()
