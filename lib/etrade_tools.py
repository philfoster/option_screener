import pyetrade
import json
import time
import datetime
from os.path import expanduser
from screener_tools import *

PROPERTIES_CREDENTIALS_FILE="credentials"
PROPERTIES_AUTHTOKEN_FILE="authtoken"
PROPERTIES_CONSUMER_KEY="CONSUMER_KEY"
PROPERTIES_CONSUMER_SECRET="CONSUMER_SECRET"
PROPERTIES_SANDBOX="SANDBOX"
PROPERTIES_LAST_AUTH_TIME="last_auth_time"
PROPERTIES_OAUTH_TOKEN="oauth_token"
PROPERTIES_OAUTH_TOKEN_SECRET="oauth_token_secret"
MAX_AUTH_TIME=120 * 60
MIN_AUTH_RENEW_THRESHOLD=15 * 60

class ETradeConfigurationError(Exception):
    """ Exception for configuration files """
    pass

class OptionChainNotFoundError(Exception):
    pass

class SymbolNotFoundError(Exception):
    pass

################################################################################
# Public methods
################################################################################
def authenticate (consumer_key,consumer_secret):
    """ Provide a user with an URL, and then prompt for the verifier code, return the auth token """
    oauth = pyetrade.ETradeOAuth(consumer_key, consumer_secret)
    print(oauth.get_request_token())

    verifier_code = input("Enter verification code: ")
    return oauth.get_access_token(verifier_code)

def get_quote(config_file, symbol, screener_config=None):
    """ Returns a quote for the symbol as a float """
    quote_data = get_quote_data(config_file, symbol)

    if quote_data.get("QuoteResponse").get("QuoteData") is None:
        raise SymbolNotFoundError(f"symbol {symbol} is not found")

    return Quote(quote_data,screener_config)

def get_quote_data(config_file, symbol):
    """ takes in an etrade json config file and a symbol, returns the quote data as a json object """
    authtoken_data = _get_authtoken(config_file)
    market = _get_market(authtoken_data)
    return market.get_quote([symbol],resp_format='json')

def get_option_chain(config_file, symbol, expiration_date):
    """ takes in an etrade json config file and a symbol and an expiration date
        returns the option chain data as a json object """
    authtoken_data = _get_authtoken(config_file)
    market = _get_market(authtoken_data)
    option_chain = None
    try:
        option_chain = OptionChain(symbol,market.get_option_chains(symbol,expiry_date=expiration_date,resp_format='json'))
    except Exception:
        raise OptionChainNotFoundError(f"could not find option chain for {expiration_date}")
    return option_chain

def get_next_monthly_expiration():
    """ Returns a datetime object for the options expiration date"""
    now = datetime.datetime.now()
    third_friday = get_third_friday(now.year,now.month)

    if now < third_friday:
        return third_friday
    else:
        if now.month < 12:
            return get_third_friday(now.year,now.month + 1)
        else:
            return get_third_friday(now.year+1,1)
        
def get_third_friday(year,month):
    first = datetime.datetime(year,month,1)
    WEEKDAY_SATURDAY = 5
    if first.weekday() < WEEKDAY_SATURDAY:
        return datetime.datetime(first.year,first.month,19-first.weekday(),23,59,59)
    else:
        return datetime.datetime(first.year,first.month,26-first.weekday(),23,59,59)
    
def renew_authtoken(config_file,force_renew):
    (creds_file, authtoken_file) = _get_etrade_config(config_file)
    authtoken_data = _get_authtoken_data(config_file)

    elapsed_time = int(time.time() - authtoken_data.get(PROPERTIES_LAST_AUTH_TIME,0))
    if force_renew or elapsed_time > MIN_AUTH_RENEW_THRESHOLD:
        # Setting up the object used for Access Management
        authManager = pyetrade.authorization.ETradeAccessManager(
                    authtoken_data.get(PROPERTIES_CONSUMER_KEY),
                    authtoken_data.get(PROPERTIES_CONSUMER_SECRET),
                    authtoken_data.get(PROPERTIES_OAUTH_TOKEN),
                    authtoken_data.get(PROPERTIES_OAUTH_TOKEN_SECRET)
                )

        authManager.renew_access_token()

        # Update the timestamp
        authtoken_data[PROPERTIES_LAST_AUTH_TIME] = int(time.time())

        # Rewrite the token file
        _write_authtoken_file(authtoken_file,authtoken_data)
        return
    return

################################################################################
# Private methods
################################################################################

def _read_properties(props_file):
    """ Read in a properties file and return a dictionary """
    with open(expanduser(props_file), "r", encoding="utf-8") as f:
        props = {e[0]: e[1] for e in [line.split('#')[0].strip().split('=') for line in f] if len(e) == 2}
    return props

def _read_etrade_json(config_file):
    """ Read in an etrade json config file and return it """
    return read_json_file(config_file)

def _get_market(authtoken_data):
    """ Create a market object from the authtoken data """
    return pyetrade.ETradeMarket( 
            authtoken_data.get(PROPERTIES_CONSUMER_KEY,None), 
            authtoken_data.get(PROPERTIES_CONSUMER_SECRET,None), 
            authtoken_data.get(PROPERTIES_OAUTH_TOKEN,None), 
            authtoken_data.get(PROPERTIES_OAUTH_TOKEN_SECRET,None), 
            dev=authtoken_data.get(PROPERTIES_SANDBOX,True)) 

def _get_etrade_config(config_file):
    """ takes in an etrade json config file and returns the credentials file path and authtoken file path """
    config_data = _read_etrade_json(config_file)

    creds_file = config_data.get(PROPERTIES_CREDENTIALS_FILE,None)
    authtoken_file = config_data.get(PROPERTIES_AUTHTOKEN_FILE,None)

    if creds_file == None:
        raise ETradeConfigurationError(f"property '{PROPERTIES_CREDENTIALS_FILE}' not defined in {config_file}")

    if authtoken_file == None:
        raise ETradeConfigurationError(f"property '{PROPERTIES_AUTHTOKEN_FILE}' not defined in {config_file}")

    return (creds_file,authtoken_file)

def _get_etrade_credentials(creds_file):
    """ Reads the credentials file and extracts the key, secret and sandbox value """
    properties = _read_properties(creds_file)
    consumer_key = properties.get(PROPERTIES_CONSUMER_KEY,None)
    consumer_secret = properties.get(PROPERTIES_CONSUMER_SECRET,None)
    sandbox = properties.get(PROPERTIES_SANDBOX,None)

    if consumer_key is None:
        raise ETradeConfigurationError(f"property '{PROPERTIES_CONSUMER_KEY}' not defined in {creds_file}")

    if consumer_secret is None:
        raise ETradeConfigurationError(f"property '{PROPERTIES_CONSUMER_SECRET}' not defined in {creds_file}")

    if sandbox == "0":
        sandbox = False
    else:
        sandbox = True

    return(consumer_key,consumer_secret,sandbox)

def _read_authtoken_file(authtoken_file):
    try:
        authtoken_data = read_json_file(authtoken_file)
    except OSError:
        return None
    except json.decoder.JSONDecodeError:
        return None

    # Validate that the authtoken file as all the correct values
    if authtoken_data.get(PROPERTIES_CONSUMER_KEY,None) is None:
        return None
    if authtoken_data.get(PROPERTIES_CONSUMER_SECRET,None) is None:
        return None
    if authtoken_data.get(PROPERTIES_SANDBOX,None) is None:
        return None
    if authtoken_data.get(PROPERTIES_OAUTH_TOKEN,None) is None:
        return None
    if authtoken_data.get(PROPERTIES_OAUTH_TOKEN_SECRET,None) is None:
        return None
    if authtoken_data.get(PROPERTIES_LAST_AUTH_TIME,None) is None:
        return None

    return authtoken_data

def _write_authtoken_file(authtoken_file,token_data):
    write_json_file(authtoken_file,token_data)

def _generate_authtoken(authtoken_file,consumer_key,consumer_secret,sandbox):
    authtoken_data = authenticate(consumer_key,consumer_secret)

    # Add in the rest of the data
    authtoken_data[PROPERTIES_LAST_AUTH_TIME] = int(time.time())
    authtoken_data[PROPERTIES_CONSUMER_KEY] = consumer_key
    authtoken_data[PROPERTIES_CONSUMER_SECRET] = consumer_secret
    authtoken_data[PROPERTIES_SANDBOX] = sandbox

    _write_authtoken_file(authtoken_file,authtoken_data)

    return authtoken_data

def _get_authtoken_data(config_file):
    (creds_file, authtoken_file) = _get_etrade_config(config_file)
    (consumer_key, consumer_secret, sandbox) = _get_etrade_credentials(creds_file)
    
    return _read_authtoken_file(authtoken_file)


def _get_authtoken(config_file):
    """ Returns a valid auth token (from cache, if available) """
    (creds_file, authtoken_file) = _get_etrade_config(config_file)
    authtoken_data = _get_authtoken_data(config_file)

    if authtoken_data is None:
        (creds_file, authtoken_file) = _get_etrade_config(config_file)
        (consumer_key, consumer_secret, sandbox) = _get_etrade_credentials(creds_file)
        return _generate_authtoken(authtoken_file,consumer_key,consumer_secret,sandbox)
    elif int(time.time() - authtoken_data.get(PROPERTIES_LAST_AUTH_TIME,0)) > MAX_AUTH_TIME:
        consumer_key = authtoken_data.get(PROPERTIES_CONSUMER_KEY)
        consumer_secret = authtoken_data.get(PROPERTIES_CONSUMER_SECRET)
        sandbox = authtoken_data.get(PROPERTIES_SANDBOX)

        return _generate_authtoken(authtoken_file,consumer_key,consumer_secret,sandbox)

    renew_authtoken(config_file,False)
    return authtoken_data

class Quote():
    def __init__(self,quote_data,screener_config=None):
        self._quote_data = quote_data

        self._symbol = self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("Product").get("symbol")
        self._price = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("lastTrade"))
        self._bid = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("bid"))
        self._ask = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("ask"))
        self._bid_size = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("bidSize"))
        self._ask_size = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("askSize"))

        self._day_high = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("high"))
        self._52week_high = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("high52"))
        self._52week_high_date = datetime.datetime.fromtimestamp(int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("week52HiDate")))
        self._day_low = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("low"))
        self._52week_low = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("low52"))
        self._52week_low_date = datetime.datetime.fromtimestamp(int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("week52LowDate")))

        self._prev_close = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("previousClose"))
        self._change_close = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("changeClose"))
        self._change_close_prct = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("changeClosePercentage"))

        self._company_name = self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("companyName")
        self._avg_vol = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("averageVolume"))
        self._volume = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("totalVolume"))
        self._beta = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("beta"))
        self._market_cap = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("marketCap"))
        self._float = int(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("sharesOutstanding"))

        # TODO - yield, dividend, ex-date, div pay date(epoch seconds), p/e ratio, eps, estEarning, 
        # TODO - after hours data (price, bid, ask, volume, change%)
        self._sector = "unknown"
        if screener_config:
            self._sector = get_sector_from_cache(screener_config,self._symbol)

    def get_symbol(self):
        return self._symbol

    def get_sector(self):
        return self._sector

    def get_price(self):
        return self._price

    def get_prev_close(self):
        return self._prev_close

    def get_change_close(self):
        return self._change_close

    def get_change_close_prct(self):
        return self._change_close_prct

    def get_volume(self):
        return self._volume

    def get_average_volume(self):
        return self._avg_vol

    def get_market_cap(self):
        cap = self._market_cap
        if cap > 10**9:
            cap = f"{cap / 10**9:.1f}B"
        elif cap > 10**6:
            cap = f"{cap / 10**6:.1f}M"
        return cap

    def get_float(self):
        fl = self._float
        if fl > 10**9:
            fl = f"{fl / 10**9:.1f}B"
        elif fl > 10**6:
            fl = f"{fl / 10**6:.1f}M"
        return fl

    def get_bid(self):
        return self._bid

    def get_bid_size(self):
        return self._bid_size

    def get_ask(self):
        return self._ask

    def get_ask_size(self):
        return self._ask_size

    def get_company_name(self):
        return self._company_name

    def get_beta(self):
        return self._beta

    def get_day_high(self):
        return self._day_high

    def get_52week_high(self):
        return self._52week_high

    def get_52week_high_date(self):
        d = self._52week_high_date
        return f"{d.year}-{d.month:02d}-{d.day:02d}"

    def get_day_low(self):
        return self._day_low

    def get_52week_low(self):
        return self._52week_low

    def get_52week_low_date(self):
        d = self._52week_low_date
        return f"{d.year}-{d.month:02d}-{d.day:02d}"


class OptionChain():
    def __init__(self,symbol,option_data):
        self._symbol = symbol
        self._option_data = option_data

        exp_year = int(option_data.get("OptionChainResponse").get("SelectedED").get("year"))
        exp_month = int(option_data.get("OptionChainResponse").get("SelectedED").get("month"))
        exp_day = int(option_data.get("OptionChainResponse").get("SelectedED").get("day"))
        self._expiration = datetime.datetime(year=exp_year,month=exp_month,day=exp_day)

        self._call_options = dict()
        self._put_options = dict()
        self._strike_prices = set()

        # For determining Put/Call Ratio
        self._put_open_interest = 0
        self._call_open_interest = 0

        self._parse_option_pairs()

        self._calculate_max_pain()

    def get_symbol():
        return self._symbol

    def _parse_option_pairs(self):
        min_dollars = 0
        for option in self._option_data.get("OptionChainResponse").get("OptionPair"):
            self._add_option(CallOption(option.get("Call")))
            self._add_option(PutOption(option.get("Put")))

    def get_option_data(self):
        return self._option_data

    def get_expiration(self):
        return self._expiration

    def _add_option(self,option):
        strike = option.get_strike_price()
        self._strike_prices.add(strike)

        if isinstance(option,CallOption):
            self._call_options[strike] = option
            self._call_open_interest += option.get_open_interest()
        elif isinstance(option,PutOption):
            self._put_options[strike] = option
            self._put_open_interest += option.get_open_interest()

    def get_strike_prices(self):
        return sorted(self._strike_prices)

    def get_call_option(self,strike):
        return self._call_options.get(strike)

    def get_put_option(self,strike):
        return self._put_options.get(strike)

    def get_put_call_ratio(self):
        return float(self._put_open_interest) / float(self._call_open_interest)

    def _calculate_max_pain(self):
        min_dollars = 0
        max_pain_strike = None
        for working_strike in self.get_strike_prices():
            put_dollars = 0
            call_dollars = 0
            for strike in self.get_strike_prices():
                price_delta = working_strike - strike

                if price_delta > 0:
                    # Calls are in the money
                    call_oi = 0
                    try:
                        call_oi = self.get_call_option(strike).get_open_interest()
                    except:
                        pass
                    call_dollars += (price_delta * call_oi * 100)
                elif price_delta < 0:
                    # Puts are in the money
                    put_oi = 0
                    try:
                        put_oi = self.get_put_option(strike).get_open_interest()
                    except:
                        pass
                    put_dollars += (price_delta * put_oi * -100)
            total_strike_dollars = call_dollars + put_dollars

            if max_pain_strike is None or (total_strike_dollars < min_dollars):
                min_dollars = total_strike_dollars
                max_pain_strike = working_strike

        self._max_pain = max_pain_strike

    def get_max_pain(self):
        return self._max_pain

class OptionChainOption():
    def __init__(self,option_data):
        self._option_data = option_data

    def get_display_symbol(self):
        return self._option_data.get("displaySymbol")

    def get_strike_price(self):
        return float(self._option_data.get("strikePrice"))

    def get_bid(self):
        return float(self._option_data.get("bid"))

    def get_ask(self):
        return float(self._option_data.get("ask"))

    def get_last_price(self):
        return float(self._option_data.get("lastPrice"))

    def get_volume(self):
        return int(self._option_data.get("volume"))

    def get_open_interest(self):
        return int(self._option_data.get("openInterest"))

    def get_adjusted_flag(self):
        return bool(self._option_data.get("adjustedFlag"))

    def get_theta(self):
        return float(self._option_data.get("OptionGreeks").get("theta"))

    def get_delta(self):
        return float(self._option_data.get("OptionGreeks").get("delta"))

    def get_symbol(self):
        return self._option_data.get("optionRootSymbol")


class CallOption(OptionChainOption):
    pass

class PutOption(OptionChainOption):
    pass
