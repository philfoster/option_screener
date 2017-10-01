#! /usr/bin/python

from urlgrabber import urlread
import time
import re
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
MAX_ATTEMPTS = 3
BASE_URL = "http://www.marketwatch.com/investing/stock/"
OUTPUT_BASENAME = "./call_options"

def get_symbols ( filename ):
    symbols = list()
    try:
        f = file ( filename )
    except IOError as e:
        logging.error ( "Error: {0}".format ( e ) )
        print "Error: {0}".format ( e )
        exit ( 1 )

    for line in f:
        symbols.append ( line.rstrip() )

    return symbols

def get_details ( symbol ):
    details = dict()
    details["symbol"] = symbol
    details["Yield"] = "0.0"
    details["Ex-Dividend Date"] = "None"
    details["P/E Ratio"] = 99999
    details_url = "{0}{1}".format ( BASE_URL, symbol )
    page_data = fetch_url ( details_url )

    #<li class="kv__item">
    #    <small class="kv__label">Rev. per Employee</small>
    #    <span class="kv__value kv__primary ">$604.23K</span>
    #    <span class="kv__value kv__secondary no-value"></span>
    #    </li>
    
    current_key = None
    parsing_value = 0
    for line in page_data.splitlines():
        # Check for the meta tags
        match = re.search ( '<meta name="([^"]+)" content="([^"]+)">', line )
        if match:
            key = match.group(1)
            value = match.group(2)
            if key == "price":
                details[key] = value.replace (',', "" )
            continue

        # Check for the values in the grids
        key_match = re.search ( '<small class="kv__label">\s*(.*\S)\s*</small>', line )
        if key_match:
            current_key = key_match.group(1)
            parsing_value = 1
            continue

        if parsing_value:
            val_match = re.search ( '<span class="kv__value kv__primary ">\s*(.*\S)\s*</span>', line )
            if val_match:
                parsing_value = 0
                details[current_key] = val_match.group(1)
            continue
            
        
    return details

def get_option_calls ( symbol, price, args ):
    min_days = args.min_days
    option_data = dict()
    options_url = "https://finance.yahoo.com/quote/{0}/options?p={0}".format ( symbol )
    now = time.time()
    for date in get_option_dates ( options_url ):

        # Skip dates too soon
        if ( date - now ) < ( 86400 * min_days ):
            logging.info ( "Date({0}): {1}({2}) is too soon".format( symbol, date, time.strftime('%y-%m-%d', time.gmtime(date) ) ) )
            continue

        # Skip dates too far
        if ( date - now ) > ( 86400 * args.max_days ):
            logging.info ( "Date({0}): {1}({2}) is too far in the future".format( symbol, date, time.strftime('%y-%m-%d', time.gmtime(date) ) ) )
            continue

        date_string = time.strftime('%Y-%m-%d',  time.gmtime(date))
        logging.debug ( "fetching option chain for {0}/{1}".format ( symbol, date_string ) )
        data = get_option_chain_by_date ( symbol, date, price, args )

        option_data[date_string] = data
    return option_data

def get_option_chain_by_date ( symbol, date, price, args ):
    calls = dict()
    url = "https://finance.yahoo.com/quote/{0}/options?p={0}&date={1}".format ( symbol, date )

    page_data = fetch_url ( url )
    for call in re.findall ( '(href="/quote/\S+\d+C\d+\?p=)', page_data ):
        match = re.search ( 'quote/(\S+)\?p=', call )
        if match:
            call_id = match.group(1)
            call_data = get_call_data ( symbol, call_id, price, args )
            if call_data:
                calls[call_id] = call_data

    return calls

def get_call_data ( symbol, call_id, price, args ):
    call_data = dict()
    call_data["ask"] = "unknown"
    call_data["bid"] = "unknown"
    call_data["strikePrice"] = "unknown"
    call_data["openInterest"] = 0
    url = "https://finance.yahoo.com/quote/{0}?p={0}".format ( call_id )

    page_data = fetch_url ( url )

    ask_match = re.search ( '"ask":{"raw":([\d\.]+),', page_data )
    if ask_match:
        call_data["ask"] = float(ask_match.group(1))

    bid_match = re.search ( '"bid":{"raw":([\d\.]+),', page_data )
    if bid_match:
        call_data["bid"] = float(bid_match.group(1))

    strike_match = re.search ( '"strikePrice":{"raw":([\d\.]+),', page_data )
    if strike_match:
        call_data["strikePrice"] = float(strike_match.group(1))

    int_match = re.search ( '"openInterest":{"raw":([\d\.]+),', page_data )
    if int_match:
        call_data["openInterest"] = int(int_match.group(1))

    if call_data["ask"] == "unknown":
        logging.info ( "Skipping call id '{0}', ask price is unknown".format ( call_id ) )
        return None

    if float(call_data["ask"]) > args.max_ask:
        logging.info ( "Skipping call id '{0}', ask price is too high ({1})".format( call_id, call_data["ask"] ) )
        return None

    if float(call_data["ask"]) <= args.min_ask:
        logging.info ( "Skipping call id '{0}', ask price is too low ({1})".format( call_id, call_data["ask"] ) )
        return None

    if call_data["openInterest"] < args.min_open_interest:
        logging.info ( "Skipping call id '{0}', open interest is too low ({1})".format ( call_id, call_data["openInterest"] ) )
        return None

    # Check to see if it's a viable call
    # It should not take more than 2% climb in price to break even
    break_even = float(call_data["strikePrice"]) + float(call_data["ask"])

    # Setup factors
    min_break_even_factor = 1 + ( args.break_even_percent / 100.0 )
    min_target_price_factor = 1 + ( args.min_target_price_percent / 100.0 )
    target_price_factor = 1 + ( args.target_price_percent / 100.0 )

    min_viable_move = price * min_break_even_factor
    logging.info ( "Examining {0} call ask {1} - break even at {2}".format ( call_data["strikePrice"], call_data["ask"], break_even ) )
    if  break_even > min_viable_move:
        logging.info ( "Skipping call id '{0}', break even point ({1}) is higher than price ({2}) plus {3}% ({4})".format ( call_id, break_even, price, args.break_even_percent, min_viable_move) )
        return None

    # Check to see if a 5% upswing yields a big enough gain
    cost_to_buy = 100 * call_data["ask"] + args.commission_cost
    target_price = price * target_price_factor
    gain_at_target_price = target_price - price
    proceeds = ( gain_at_target_price * 100 ) - args.commission_cost

    if proceeds < ( cost_to_buy * min_target_price_factor ):
        logging.info ( "Skipping call id '{0}', proceeds ({1}) are less than minimum target price factor ({2})".format ( call_id, proceeds, cost_to_buy * min_target_price_factor ) )
        return None

    return call_data

def get_option_dates ( url ):
    dates = list()
    page_data = fetch_url ( url )
    for option_string in re.findall ( '(<option value="\d+" data-reactid="\d+">\S+\s+\d+, 20\d\d</option>)', page_data ):
        match = re.search ( 'option value="(\d+)"', option_string )
        if match:
            dates.append ( int( match.group(1) ) )
    return dates
    
def fetch_url ( url ):
    # Slow this pig down a little
    time.sleep ( 1 )
    logging.debug ( "Fetching {0}".format( url ) )
    page_data = None
    attempts = 1
    while ( attempts <= MAX_ATTEMPTS ):
        try:
            page_data = urlread ( url )
            break
        except Exception as e:
            logging.error ( "Error: {0}".format(e) )
            print "Error: {0}".format(e)
            attempts = attempts + 1
            time.sleep ( 5 )

    return page_data

def get_viable_options ( symbols, args ):
    viable_calls = set()

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
        data["call_options"] = get_option_calls ( symbol, float(data["price"]), args )
        logging.debug ( data )
        
        for date_key in data["call_options"]:
            for call_id in data["call_options"][date_key]:
                bid = data["call_options"][date_key][call_id]["bid"]
                ask = data["call_options"][date_key][call_id]["ask"]
                strike = data["call_options"][date_key][call_id]["strikePrice"]
                print "Viable option: {0} {1} {2} call ask {3}".format( symbol, date_key, strike, ask )
                logging.info ( "Viable option: {0} {1} {2} call ask {3}".format( symbol, date_key, strike, ask ) )

                good_call = (symbol,data["price"],data["P/E Ratio"],data["Yield"],data["Ex-Dividend Date"],date_key,strike,ask)
                viable_calls.add ( good_call )

    return viable_calls


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

    viable_calls = get_viable_options ( symbol_list, args )

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
