#! /usr/bin/python

from urlgrabber import urlread
import time
import re

min_open_interest = 10
max_ask = 10
max_days = 45
min_days = 21
max_attempts = 3

base_url = "http://www.marketwatch.com/investing/stock/"

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

def get_option_calls ( symbol ):
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

		data = get_option_chain_by_date ( symbol, date )
		option_data[date] = data
	return option_data

def get_option_chain_by_date ( symbol, date ):
	calls = dict()
	url = "https://finance.yahoo.com/quote/{0}/options?p={0}&date={1}".format ( symbol, date )

	page_data = fetch_url ( url )
	for call in re.findall ( '(href="/quote/\S+\d+C\d+\?p=)', page_data ):
		match = re.search ( 'quote/(\S+)\?p=', call )
		if match:
			call_id = match.group(1)
			call_data = get_call_data ( symbol, call_id )
			if call_data:
				calls[call_id] = call_data

	return calls

def get_call_data ( symbol, call_id ):
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
		call_data["ask"] = ask_match.group(1)

	bid_match = re.search ( '"bid":{"raw":([\d\.]+),', page_data )
	if bid_match:
		call_data["bid"] = bid_match.group(1)

	strike_match = re.search ( '"strikePrice":{"raw":([\d\.]+),', page_data )
	if strike_match:
		call_data["strikePrice"] = strike_match.group(1)

	int_match = re.search ( '"openInterest":{"raw":([\d\.]+),', page_data )
	if int_match:
		call_data["openInterest"] = int(int_match.group(1))

	if call_data["ask"] == "unknown":
		print "Skipping call id '{0}', ask price is unknown".format ( call_id )
		return None

	if float(call_data["ask"]) > max_ask:
		print "Skipping call id '{0}', ask price is too high ({1})".format( call_id, call_data["ask"] )
		return None

	if call_data["openInterest"] < min_open_interest:
		print "Skipping call id '{0}', open interest is too low ({1})".format ( call_id, call_data["openInterest"] )
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
		except Error as e:
			print "Error: {0}".format(e)
			attempts = attempts + 1
			time.sleep ( 5 )

	return page_data

symbols = get_symbols ( "symbols.txt" )

for symbol in symbols:
	# Details data
	data = get_details ( symbol )

	# Option chain
	data["option_calls"] = get_option_calls ( symbol )
	print data
	
