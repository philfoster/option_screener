from urlgrabber import urlread
import re
import time
import logging

DETAILS_URL = "http://www.marketwatch.com/investing/stock/"
MAX_ATTEMPTS = 3

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
    details["price"] = "0.0"
    details["Ex-Dividend Date"] = "None"
    details["P/E Ratio"] = 99999
    details_url = "{0}{1}".format ( DETAILS_URL, symbol )
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

def get_put_options ( symbol, price, args ):
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
            logging.info ( "Date({0}): {1}({2}) is too far in the future (max_days={3})".format( symbol, date, time.strftime('%y-%m-%d', time.gmtime(date) ), args.max_days ) )
            continue

        date_string = time.strftime('%Y-%m-%d',  time.gmtime(date))
        logging.debug ( "fetching option chain for {0}/{1}".format ( symbol, date_string ) )
        data = get_put_option_chain_by_date ( symbol, date, price, args )

        option_data[date_string] = data
    return option_data

def get_call_options ( symbol, price, args ):
    logging.debug ( "Fetching option chain" )
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
        data = get_call_option_chain_by_date ( symbol, date, price, args )

        option_data[date_string] = data
    return option_data

def get_put_option_chain_by_date ( symbol, date, price, args ):
    puts = dict()
    url = "https://finance.yahoo.com/quote/{0}/options?p={0}&date={1}".format ( symbol, date )

    page_data = fetch_url ( url )
    for put in re.findall ( '(href="/quote/\S+\d+P\d+\?p=)', page_data ):
        match = re.search ( 'quote/(\S+)\?p=', put )
        if match:
            put_id = match.group(1)
            put_data = get_put_data ( symbol, put_id, price, args )
            if put_data:
                puts[put_id] = put_data

    return puts

def get_call_option_chain_by_date ( symbol, date, price, args ):
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

def get_put_data ( symbol, put_id, price, args ):
    put_data = dict()
    put_data["ask"] = 0.0
    put_data["bid"] = 0.0
    put_data["strikePrice"] = 0.0
    put_data["openInterest"] = 0
    url = "https://finance.yahoo.com/quote/{0}?p={0}".format ( put_id )

    page_data = fetch_url ( url )

    ask_match = re.search ( '"ask":{"raw":([\d\.]+),', page_data )
    if ask_match:
        put_data["ask"] = float(ask_match.group(1))

    bid_match = re.search ( '"bid":{"raw":([\d\.]+),', page_data )
    if bid_match:
        put_data["bid"] = float(bid_match.group(1))

    strike_match = re.search ( '"strikePrice":{"raw":([\d\.]+),', page_data )
    if strike_match:
        put_data["strikePrice"] = float(strike_match.group(1))

    int_match = re.search ( '"openInterest":{"raw":([\d\.]+),', page_data )
    if int_match:
        put_data["openInterest"] = int(int_match.group(1))

    if put_data["ask"] == "unknown":
        logging.info ( "Skipping put id '{0}', ask price is unknown".format ( put_id ) )
        return None

    # Check to see if it's a viable put
    return put_data

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

    # Totally just faking this now
    #dates.append ( 1507248000 ); # Oct 6th
    #dates.append ( 1507852800 ); # Oct 13th
    #dates.append ( 1508457600 ); # Oct 20th
    #dates.append ( 1509062400 ); # Oct 27th
    dates.append ( 1509667200 ); # Nov 3rd
    dates.append ( 1510272000 ); # Nov 10th
    dates.append ( 1510876800 ); # Nov 17th
    dates.append ( 1513296000 ); # Dec 15th

    for count in range (1,100):
        dates.append ( 1513296000 + ( count * 7 * 86400 ) );
    
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

def get_safe_calls ( symbols, args ):
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
        data["call_options"] = get_call_options ( symbol, float(data["price"]), args )
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

def get_earnings_miss_puts ( symbols, args ):
    viable_puts = set()
    for symbol in symbols:
        logging.info ( "Looking for options on {0}".format ( symbol ) )
        print "Looking for options on {0}".format ( symbol )
        # Details data
        data = get_details ( symbol )

        # Option chain
        data["put_options"] = get_put_options ( symbol, float(data["price"]), args )
        logging.info ( data )

        for date_key in data["put_options"]:
            for put_id in data["put_options"][date_key]:
                bid = data["put_options"][date_key][put_id]["bid"]
                ask = data["put_options"][date_key][put_id]["ask"]
                strike = data["put_options"][date_key][put_id]["strikePrice"]
                open_interest = data["put_options"][date_key][put_id]["openInterest"]

                if ask > args.max_ask:
                    logging.info ( "Skipping put id '{0}', ask price is too high ({1})".format( put_id, ask ) )
                    continue

                if ask <= args.min_ask:
                    logging.info ( "Skipping put id '{0}', ask price is too low ({1})".format( put_id, ask ) )
                    continue

                if open_interest < args.min_open_interest:
                    logging.info ( "Skipping put id '{0}', open interest is too low ({1})".format ( put_id, open_interest ) )
                    continue


                # Setup factors
                min_break_even_factor = 1 - ( args.break_even_percent / 100.0 )
                min_target_price_factor = 1 - ( args.min_target_price_percent / 100.0 )
                target_price_factor = 1 - ( args.target_price_percent / 100.0 )

                min_viable_move = float(data["price"]) * min_break_even_factor

                break_even_price = strike - ask

                # If stock lost X% what would the price be?
                target_price = float(data["price"]) * target_price_factor
                cost_to_buy = ( 100 * ask ) + args.commission_cost

                gain_at_target_price = float(data["price"]) - target_price
                proceeds = ( gain_at_target_price * 100 ) - args.commission_cost

                if min_viable_move > break_even_price:
                    logging.info ( "Skipping put id '{0}', price({1}) minus {2}% loss({3}) is higher than break even price({4})".format ( put_id, data["price"], args.break_even_percent, min_viable_move, break_even_price ) )
                    continue
            
                if proceeds < ( cost_to_buy * min_target_price_factor ):
                    logging.info ( "Skipping put id '{0}', proceeds ({1}) are less than minimum target price factor ({2})".format ( put_id, proceeds, cost_to_buy * min_target_price_factor ) )
                    continue

                print "Viable option: {0} {1} {2} put ask {3}".format( symbol, date_key, strike, ask )
                logging.info ( "Viable option: {0} {1} {2} put ask {3}".format( symbol, date_key, strike, ask ) )

                good_put = (symbol,data["price"],data["P/E Ratio"],data["Yield"],data["Ex-Dividend Date"],date_key,strike,ask)
                viable_puts.add ( good_put )
        
    return viable_puts

def get_itm_call_option_chain_by_date ( symbol, date, price, args ):
    calls = dict()
    url = "https://finance.yahoo.com/quote/{0}/options?p={0}&date={1}".format ( symbol, date )

    page_data = fetch_url ( url )
    for call in re.findall ( '(href="/quote/\S+\d+C\d+\?p=)', page_data ):
        match = re.search ( 'quote/(\S+)\?p=', call )
        if match:
            call_id = match.group(1)
            call_data = get_itm_call_data ( symbol, call_id, price, args )
            if call_data:
                calls[call_id] = call_data

    return calls

def get_itm_call_options ( symbol, price, args ):
    logging.debug ( "Fetching option chain" )
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
            remaining = int ( ( date - now ) / 86400 )
            logging.info ( "Date({0}): {1}({2}) is too far in the future (max_days={3})".format( symbol, date, time.strftime('%y-%m-%d', time.gmtime(date) ), args.max_days ) )
            continue

        date_string = time.strftime('%Y-%m-%d',  time.gmtime(date))
        logging.debug ( "fetching option chain for {0}/{1}".format ( symbol, date_string ) )
        data = get_itm_call_option_chain_by_date ( symbol, date, price, args )

        option_data[date_string] = data

    exit

    return option_data

def get_itm_call_data ( symbol, call_id, price, args ):
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

    return call_data

