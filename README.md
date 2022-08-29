# option_screener
	This project is meant to provide tools for finding covered call options 
	that meet specific criteria around goals and market tone.

	The scripts require an E*Trade API authtoken. When created, the auth token is 
	cached for a period of two hours. If one of the scripts uses the auth
	token it is refreshed (a maximum of one refresh per five minutes). If
	no valid auth token exists, you'll be given a URL to paste into a 
	browser, where you authenticate and are given a code. Paste the code
	at the prompt to cache the auth token.

	This project is heavily inspired by Alan Ellman (The Blue Collar Investor)
	To understand the goals laid out here, watch his youtube videos on 
	'Beginner's Corner for Covered Call Writing' or visit his website at
	https://www.thebluecollarinvestor.com

# Requirements
	This code requires the excellent pyetrade API from Jesse Cooper
	https://github.com/jessecooper/pyetrade

	Additionally, this module requires an active E*Trade account and an
	API key (available from E*Trade customer service)

	ata.py requires stock_chart_tools package from pypi for calculating
	the technicals indicators like macd, obv, slow stochastics and 
	exponential moving averages.
	https://pypi.org/project/stock-chart-tools/0.1.0/
	https://github.com/philfoster/stock_chart_tools

# scripts and tools
	bin/get_quote.py  -- Get a real time quote for a symbol
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

	bin/ccw_screener.py  -- Search the option chain for a symbol for call options that match the criteria
		$ bin/ccw_screener.py -h
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
		  -d, --debug           Enable debugging
		  -v, --verbose         Increase verbosity
		  -m MARKET_TONE, --market-tone MARKET_TONE
					Market tone configuration

		$ bin/ccw_screener.py -e 2021-04-16 -v -m tone/market-neutral.json -s AMAT
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

	bin/stock_screener.py  -- Loop across symbols in a directory of watch lists, filter the results based
							 on a number of configurable questions. The question has an expiration time
							 to prevent asking the same question with the cached answer is still fresh.
		usage: stock_screener.py [-h] [-c CONFIG_FILE] [-v] [-q] [-o OUTPUT_FILE]
								 [-r REVIEW_SYMBOL] [-s SYMBOL]

		$ bin/stock_screener.py --help
		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
								etrade configuration file
		  -v, --verbose         Increase verbosity
		  -q, --quote           Include a quote in the summary
		  -o OUTPUT_FILE, --output OUTPUT_FILE
								Write the results to a file
		  -r REVIEW_SYMBOL, --review REVIEW_SYMBOL
								Review a symbol's cached data
		  -s SYMBOL, --symbol SYMBOL
								Perform fresh screen of a symbol
		usage: stock_screener.py [-h] [-c CONFIG_FILE] [-v] [-q]

		$ bin/stock_screener.py
		bin/stock_screener.py

				Select a sector (ABT)

				 1. Automobiles & Auto Parts
				 2. Banking Services
				...
				17. Paper & Forest Products
				18. Pharmaceuticals
				19. Professional & Commercial Services
				20. Semiconductors
				21. Software & IT Services
				22. Textiles & Apparel

				ABT[Company Information] What sector is the stock? (or 'new' for a new sector) 18
				ABT[Fundamentals] When is the next earnings announcement? (YYYY-MM-DD): 2021-10-20
				ABT[Fundamentals] Is the average analyst rating better than neutral? [y/N] y
				ABT[Technicals] Is the stock price up trending? [y/N] y
				ABT[Technicals] Is the price above the 20 day EMA? [y/N] y
				ABT[Technicals] Is the 20 day EMA trending up? [y/N] y
				ABT[Technicals] Is the 20 day EMA above the 100 day EMA? [y/N] y
				ABT[Technicals] Is the 100 day EMA trending up? [y/N] y
				ABT[Technicals] Is the MACD trending up? [y/N] y
				ABT[Technicals] Is the MACD divergence positive? [y/N] y
				ABT[Technicals] Is the MACD greater than zero? [y/N] y
				ABT[Technicals] Is the stochastic oscilator positive? [y/N] y
				ABT[Technicals] Is the stochastic oscilator uptrending? [y/N] y
				ABT[Technicals] Is the stochastic oscilator greater than 20? [y/N] y
				ABT[Technicals] Is the On Balance Volume positive?  [y/N] y
				ABT[Technicals] Is the On Balance Volume trending up?  [y/N] y
				ABT[Technicals] Is the volume greater than than moving average?  [y/N] y

		Valid Symbols
		-------------
				A     (score= 94.74)%
				ABT   (score=100.00)%
				...

	bin/ata.py  -- Automated Technical Analysis, analyzes price trend data and 
				   updates the cache for the stock screner
					Requires: pandas, yfinance

		$ bin/ata.py --help
		usage: ata.py [-h] [-c CONFIG_FILE] [-v] [-s SYMBOL]

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
								screener configuration file
		  -v, --verbose         Increase verbosity
		  -s SYMBOL, --symbol SYMBOL
								Analyze a symbol

	bin/bull_call_spread_screener.py  -- Screen for veritical credit spreads
								that aim to generate significant return and have
								significant downside protection.

		usage: bull_call_spread_screener.py [-h] [-c CONFIG_FILE] -s SYMBOL
										[-e EXPIRATION] [-d] [-v] [-p PARAMETERS]

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
								etrade configuration file
		  -s SYMBOL, --symbol SYMBOL
								Symbol to search
		  -e EXPIRATION, --expiration EXPIRATION
								Expiration Date <YYYY-MM-DD>
		  -d, --debug           Enable debugging
		  -v, --verbose         Increase verbosity
		  -p PARAMETERS, --paramaters PARAMETERS
								Option parameters configuration

	bin/find_roll_outs.py -- Look for options that you can roll out to if you
							 	are holding an option that is in the money
								near the expiration date.


		usage: find_roll_outs.py [-h] [-c CONFIG_FILE] -s SYMBOL -e EXPIRATION -p
								 STRIKE [-v]

		optional arguments:
		  -h, --help            show this help message and exit
		  -c CONFIG_FILE, --config-file CONFIG_FILE
								etrade configuration file
		  -s SYMBOL, --symbol SYMBOL
								Symbol of the call
		  -e EXPIRATION, --expiration EXPIRATION
								Expiration Date <YYYY-MM-DD>
								Symbol to search
		  -p STRIKE, --strike-price STRIKE
								Strike price
		  -v, --verbose         Increase verbosity

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

	bull_call_spread.json
		These files contain the parameters for screening the options.
			min_open_interest - minimum number of options for viability
			min_annual_roo    - minimum annualized gain return on the option spread
			min_downside	  - minumum downside protection of the option spread
			min_short_delta	  - minumum short call delta (roughtly equates to probabilty of success)
			min_long_delta	  - minimum delta for the long call

			These parameters are set to 5% / month with 7% downside protection and 70% chance of success
		Example:
			{
				"min_open_interest": 10,
				"min_annual_roo": 0.60,
				"min_downside": 0.07,
				"min_short_delta" : 0.70,
				"min_long_delta" : 0.8
			}
