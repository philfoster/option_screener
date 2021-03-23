# option_screener
	This project is meant to provide tools for finding covered call options 
	that meet specific criteria around goals and market tone.

	The scripts require an API authtoken. When created, the auth token is 
	cached for a period of two hours. If one of the scripts uses the auth
	token it is refreshed (a maximum of one refresh per five minutes). If
	no valid auth token exists, you'll be given a URL to paste into a 
	browser, where you authenticate and are given a code. Paste the code
	at the prompt to cache the auth token.

# Requirements
	This code requires the excellent pyetrade API from Jesse Cooper
	https://github.com/jessecooper/pyetrade

# scripts
	bin/get_quote.py
		$ bin/get_quote.py -h
		usage: get_quote.py [-h] [-c CONFIG_FILE] -s SYMBOL [-v]

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
					etrade configuration file
		  -s SYMBOL, --symbol SYMBOL
					Symbol to search
		  -v, --verbose         Increase verbosity

		$ bin/get_quote.py -v -s AMAT
		AMAT (APPLIED MATLS INC COM)
			Price : $119.33 bid=$120.55(100) ask=$120.87(100)
			Volume: 11981 (avg=9520524)

	ccw_screener.py
		$ ./ccw_screener.py -h
		usage: ccw_screener.py [-h] [-c CONFIG_FILE] -s SYMBOL [-e EXPIRATION] [-d]
				       [-v] -m MARKET_TONE

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
					etrade configuration file
		  -s SYMBOL, --symbol SYMBOL
					Symbol to search
		  -e EXPIRATION, --expiration EXPIRATION
					Expiration Date <YYYY-MM-DD>
		  -d, --debug           Expiration Date <YYYY-MM-DD>
		  -v, --verbose         Increase verbosity
		  -m MARKET_TONE, --market-tone MARKET_TONE
					Market tone configuration

		$ ./ccw_screener.py -e 2021-04-16 -v -m tone/market-neutral.json -s AMAT
		AMAT Apr 16 '21 $115 Call: days=24 price=119.33 premium=$7.35(mark=7.53) cost=$11198.00 oi=2876 beta=1.78
			Protection:   3.63%             Delta :   0.6581
			ROO       :   2.63% ( 39.94%)   Profit: $ 302.00
			Upside    :   0.00% (  0.00)%   Profit: $   0.00
			Total     :   2.63% ( 39.94%)   Total : $ 302.00

		AMAT Apr 16 '21 $120 Call: days=24 price=119.33 premium=$4.70(mark=4.83) cost=$11463.00 oi=4810 beta=1.78
			Protection:   0.00%             Delta :   0.5044
			ROO       :   3.92% ( 59.57%)   Profit: $ 470.00
			Upside    :   0.56% (  8.54)%   Profit: $  67.00
			Total     :   4.48% ( 68.10%)   Total : $ 537.00

# Configuration
	etrade.json - this is the base configuration file that points to other configs
		Example:
			{
				"authtoken": "~/.etrade-authtoken.json",
				"credentials": "~/.etrade.properties"
			}

	.etrade.properties - contains your credentials (get these from etrade)
		Example:
			CONSUMER_KEY=<your consumer key>
			CONSUMER_SECRET=<your consumer secret>
			SANDBOX=0

	
	market tone json files
		These files contain the parameters for screening the options.
			min_open_interest - minimum number of options for viability
			min_annual_roo    - minimum annualized gain return on option
			max_annual_roo    - maximum annualized gain return on option (filters out super volatile stocks)
			min_annual_update - minimum annualized gain for upside on an option (>0 forces out of the money calls)
			min_downside	  - minumum downside protection of the option (>0 forced in the money calls)
			min_delta	  - minumum delta (roughly the probability of expiring in the money)
			max_delta	  - maxumum delta (roughly the probability of expiring in the money)
		Example:
			{
				"min_open_interest": 50,
				"min_annual_roo": 0.24,
				"max_annual_roo": 0.96,
				"min_annual_upside": 0.0,
				"min_downside": 0.0,
				"min_delta" : 0.45,
				"max_delta" : 0.90
			}
