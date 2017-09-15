#! /usr/bin/python

from urlgrabber import urlread
import time
import re

min_open_interest = 10
max_ask = 10
min_ask = .01
max_days = 45
min_days = 23
max_attempts = 3
max_pe_ratio = 30
min_yield = 1
max_price = 400

break_even_percent = 2
min_break_even_factor = 1 + ( break_even_percent / 100.0 )

min_target_price_percent = 20
min_target_price_factor = 1 + ( min_target_price_percent / 100.0 )

target_price_percent = 5
target_price_factor = 1 + ( target_price_percent / 100.0 )
commission_cost = 7.73

base_url = "http://www.marketwatch.com/investing/stock/"

output_csv_basename = "./call_options"

def get_symbols ( filename ):
	symbols = list()
	try:
		f = file ( filename )
	except IOError as e:
		print "Error: {0}".format ( e )
		exit ( 1 )

	for line in f:
		symbols.append ( line.rstrip() )

	return symbols

def get_details ( symbol ):
	# http://www.marketwatch.com/investing/stock/<symbol>
	details = dict()
	details["symbol"] = symbol
	details["Yield"] = "None"
	details["Ex-Dividend Date"] = "None"
	details["P/E Ratio"] = 99999
	details_url = "{0}{1}".format ( base_url, symbol )
	page_data = fetch_url ( details_url )

	#<li class="kv__item">
	#	<small class="kv__label">Rev. per Employee</small>
	#	<span class="kv__value kv__primary ">$604.23K</span>
	#	<span class="kv__value kv__secondary no-value"></span>
	#	</li>
	
	current_key = None
	parsing_value = 0
	for line in page_data.splitlines():
		# Check for the meta tags
		match = re.search ( '<meta name="([^"]+)" content="([^"]+)">', line )
		if match:
			key = match.group(1)
			value = match.group(2)
			if key == "price":
				details[key] = value
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

def get_option_calls ( symbol, price ):
	option_data = dict()
	options_url = "https://finance.yahoo.com/quote/{0}/options?p={0}".format ( symbol )
	now = time.time()
	for date in get_option_dates ( options_url ):

		# Skip dates too soon
		if ( date - now ) < ( 86400 * min_days ):
			print "Date({0}): {1} is too soon".format( symbol, date )
			continue

		# Skip dates too far
		if ( date - now ) > ( 86400 * max_days ):
			print "Date({0}): {1} is too far in the future".format( symbol, date )
			continue

		data = get_option_chain_by_date ( symbol, date, price )
		date_string = time.strftime('%Y-%m-%d',  time.gmtime(date))

		option_data[date_string] = data
	return option_data

def get_option_chain_by_date ( symbol, date, price ):
	calls = dict()
	url = "https://finance.yahoo.com/quote/{0}/options?p={0}&date={1}".format ( symbol, date )

	page_data = fetch_url ( url )
	for call in re.findall ( '(href="/quote/\S+\d+C\d+\?p=)', page_data ):
		match = re.search ( 'quote/(\S+)\?p=', call )
		if match:
			call_id = match.group(1)
			call_data = get_call_data ( symbol, call_id, price )
			if call_data:
				calls[call_id] = call_data

	return calls

def get_call_data ( symbol, call_id, price ):
	call_data = dict()
	call_data["ask"] = "unknown"
	call_data["bid"] = "unknown"
	call_data["strikePrice"] = "unknown"
	call_data["openInterest"] = 0
	url = "https://finance.yahoo.com/quote/{0}?p={0}".format ( call_id )

	print "Fetching {0}".format( call_id )
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
		print "Skipping call id '{0}', ask price is unknown".format ( call_id )
		return None

	if float(call_data["ask"]) > max_ask:
		print "Skipping call id '{0}', ask price is too high ({1})".format( call_id, call_data["ask"] )
		return None

	if float(call_data["ask"]) <= min_ask:
		print "Skipping call id '{0}', ask price is too low ({1})".format( call_id, call_data["ask"] )
		return None

	if call_data["openInterest"] < min_open_interest:
		print "Skipping call id '{0}', open interest is too low ({1})".format ( call_id, call_data["openInterest"] )
		return None

	# Check to see if it's a viable call
	# It should not take more than 2% climb in price to break even
	break_even = float(call_data["strikePrice"]) + float(call_data["ask"])

	min_viable_move = price * min_break_even_factor
	print "Examining {0} call ask {1} - break even at {2}".format ( call_data["strikePrice"], call_data["ask"], break_even )
	if  break_even > min_viable_move:
		print "Skipping call id '{0}', break even point ({1}) is higher than price ({2}) plus {3}% ({4})".format ( call_id, break_even, price, break_even_percent, min_viable_move)
		return None

	# Check to see if a 5% upswing yields a big enough gain
	cost_to_buy = 100 * call_data["ask"] + commission_cost
	target_price = price * target_price_factor
	gain_at_target_price = target_price - price
	proceeds = ( gain_at_target_price * 100 ) - commission_cost

	if proceeds < ( cost_to_buy * min_target_price_factor ):
		print "Skipping call id '{0}', proceeds ({1}) are less than minimum target price factor ({2})".format ( call_id, proceeds, cost_to_buy * min_target_price_factor )
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
	print "Fetching {0}".format( url )
	page_data = None
	attempts = 1
	while ( attempts <= max_attempts ):
		try:
			page_data = urlread ( url )
			break
		except Exception as e:
			print "Error: {0}".format(e)
			attempts = attempts + 1
			time.sleep ( 5 )

	return page_data

symbols = get_symbols ( "symbols.txt" )

viable_calls = set()

for symbol in symbols:
	# Details data
	data = get_details ( symbol )

	# Check the price
	if float(data["price"]) > max_price:
		print "Skipping {0}, price is too high {1}".format ( symbol, data["price"] )
		continue

	# Check the p/e ratio
	if float(data["P/E Ratio"]) > max_pe_ratio:
		print "Skipping {0}, P/E Ration is too high {1}".format ( symbol, data["P/E Ratio"] )
		continue

	# Check the yield
	yield_match = re.search ( '^([\d\.]+)\%?', data["Yield"] )
	if yield_match:
		div_yield = yield_match.group(1)
		if float(div_yield) < min_yield:
			print "Skipping {0}, yield is too low {1}".format ( symbol, data["Yield"] )
			continue
	else:
		print "Skipping {0}, yield is too low {1}".format ( symbol, data["Yield"] )
		continue

	# Option chain
	data["call_options"] = get_option_calls ( symbol, float(data["price"]) )
	print data
	
	print "--------------\n"
	print "Symbol: {0}".format ( symbol )
	print "Price: {0}".format ( data["price"] )
	print "P/E Ratio: {0}".format ( data["P/E Ratio"] )
	print "Yield: {0}".format ( data["Yield"] )
	print "Ex-Dividend Date: {0}".format ( data["Ex-Dividend Date"] )
	for date_key in data["call_options"]:
		for call_id in data["call_options"][date_key]:
			bid = data["call_options"][date_key][call_id]["bid"]
			ask = data["call_options"][date_key][call_id]["ask"]
			strike = data["call_options"][date_key][call_id]["strikePrice"]
			print "Viable option: {0} {1} call ask {2}".format( date_key, strike, ask )

			good_call = (symbol,data["price"],data["P/E Ratio"],data["Yield"],data["Ex-Dividend Date"],date_key,strike,ask)
			viable_calls.add ( good_call )

output_csv = "{0}-{1}.csv".format ( output_csv_basename, int(time.time()) )
f = file ( output_csv, "w" )
f.write ( "Symbol,Price,P/E Ratio,Yield,Ex-Dividend Date,Expiration Date,Strike Price,Ask,Break Even,Cost,Price at +{0}%,Proceeds at +{0}%,Gain$ at +{0}%, Gain% at +{0}%\n".format ( target_price_percent ) )

print "Writing results to {0}".format(output_csv)
for call in viable_calls:
	(symbol,price,pe_ratio,div_yield,div_date,exp_date,strike,ask) = call

	price_at_target = float(price) * target_price_factor
	gain_at_target = price_at_target - strike
	proceeds_at_target = ( gain_at_target * 100 ) - commission_cost

	cost_to_buy = ( ask * 100 ) + commission_cost

	profit_dollars = proceeds_at_target - cost_to_buy
	profit_percent = ( profit_dollars / cost_to_buy )

	f.write("{0},{1},{2},{3},\"{4}\",{5},{6},{7},{8},{9},{10},{11},{12},{13:.2%}\n".format ( symbol, price, pe_ratio, div_yield,div_date,exp_date,strike,ask,(strike + ask),cost_to_buy,price_at_target,proceeds_at_target,profit_dollars,profit_percent) )

f.close()
