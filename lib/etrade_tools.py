import pyetrade
import json
import time
import datetime
from os.path import expanduser

PROPERTIES_CREDENTIALS_FILE="credentials"
PROPERTIES_AUTHTOKEN_FILE="authtoken"
PROPERTIES_CONSUMER_KEY="CONSUMER_KEY"
PROPERTIES_CONSUMER_SECRET="CONSUMER_SECRET"
PROPERTIES_SANDBOX="SANDBOX"
PROPERTIES_LAST_AUTH_TIME="last_auth_time"
PROPERTIES_OAUTH_TOKEN="oauth_token"
PROPERTIES_OAUTH_TOKEN_SECRET="oauth_token_secret"
MAX_AUTH_TIME=90 * 60
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

def get_quote(config_file, symbol):
    """ Returns a quote for the symbol as a float """
    quote_data = get_quote_data(config_file, symbol)

    if quote_data.get("QuoteResponse").get("QuoteData") is None:
        raise SymbolNotFoundError(f"symbol {symbol} is not found")

    return Quote(quote_data)

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

def read_json_file(json_file):
    """ Read in a json file and return a json data structure """
    json_data = None
    with open(expanduser(json_file), "r") as cf:
        json_data = json.loads("".join(cf.readlines()))
    return json_data

def renew_authtoken(config_file,force_renew):
    (creds_file, authtoken_file) = _get_etrade_config(config_file)
    authtoken_data = _get_authtoken_data(config_file)

    # Setting up the object used for Access Management
    authManager = pyetrade.authorization.ETradeAccessManager(
                authtoken_data.get(PROPERTIES_CONSUMER_KEY),
                authtoken_data.get(PROPERTIES_CONSUMER_SECRET),
                authtoken_data.get(PROPERTIES_OAUTH_TOKEN),
                authtoken_data.get(PROPERTIES_OAUTH_TOKEN_SECRET)
            )

    elapsed_time = int(time.time() - authtoken_data.get(PROPERTIES_LAST_AUTH_TIME,0))
    if force_renew or elapsed_time > MIN_AUTH_RENEW_THRESHOLD:
        print("renewing authtoken")
        # Triggering a renew
        authManager.renew_access_token()

        # Update the timestamp
        authtoken_data[PROPERTIES_LAST_AUTH_TIME] = int(time.time())

        # Rewrite the token file
        _write_authtoken_file(authtoken_file,authtoken_data)
        return
    print(f"not renewing elapsed={elapsed_time}")
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
    with open(expanduser(authtoken_file), "w") as tf:
        tf.write(json.dumps(token_data))

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

    consumer_key = authtoken_data.get(PROPERTIES_CONSUMER_KEY)
    consumer_secret = authtoken_data.get(PROPERTIES_CONSUMER_SECRET)
    sandbox = authtoken_data.get(PROPERTIES_SANDBOX)

    if authtoken_data is None:
        return _generate_authtoken(authtoken_file,consumer_key,consumer_secret,sandbox)
    elif int(time.time() - authtoken_data.get(PROPERTIES_LAST_AUTH_TIME,0)) > MAX_AUTH_TIME:
        return _generate_authtoken(authtoken_file,consumer_key,consumer_secret,sandbox)

    renew_authtoken(config_file,False)
    return authtoken_data

class Quote():
    def __init__(self,quote_data):
        self._quote_data = quote_data

        self._price = float(self._quote_data.get("QuoteResponse").get("QuoteData")[0].get("All").get("lastTrade"))

    def get_price(self):
        return self._price

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

        self._parse_option_pairs()

    def get_symbol():
        return self._symbol

    def _parse_option_pairs(self):
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
        elif isinstance(option,PutOption):
            self._put_options[strike] = option

    def get_strike_prices(self):
        return sorted(self._strike_prices)

    def get_call_option(self,strike):
        return self._call_options.get(strike)

    def get_put_option(self,strike):
        return self._put_options.get(strike)

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
