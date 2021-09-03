#! /usr/bin/python3

import argparse
import datetime
import glob
import json
import re
from etrade_tools import *

DEFAULT_SCREENER_CONFIG_FILE="stock_screener.json"

# Globals
global GLOBAL_VERBOSE
global GLOBAL_QUOTE_CACHE

# Screener config items
CACHE_DIR="cache_dir"
ETRADE_CONFIG="etrade_config"
QUESTIONS_DIR="questions_directory"
SYMBOLS_DIR="symbols_directory"

# Defaults
DEFAULT_CACHE_DIR=".answers"
DEFAULT_PRICE_MIN=15.0
DEFAULT_PRICE_MAX=375.0
DEFAULT_VOLUME_MIN=400000
DEFAULT_OPEN_INTEREST_MIN=50
DEFAULT_SECTOR_FILE="~/.stock_sectors.json"

# Question configuration
QUESTION_NAME="name"
QUESTION_LIST="questions"
QUESTION_TEXT="question"
QUESTION_TYPE="type"
QUESTION_ID="uuid"
QUESTION_BLOCKER="blocker"
QUESTION_EXPIRATION_DAYS="expiration_days"
PRICE_MIN="price_min"
PRICE_MAX="price_max"
VOLUME_MIN="volume_min"
SECTOR_FILE="sector_file"
OPEN_INTEREST_MIN="open_interest_min"

# Cache constants
CACHE_SYMBOL="symbol"
CACHE_VALUE="value"
CACHE_EXPIRATION_TIMESTAMP="expiration_timestamp"
CACHE_QUESTION="question"

# Quetion types
TYPE_BOOLEAN="boolean"
TYPE_EARNINGS="earnings_date"
TYPE_SECTOR="sector_selection"
TYPE_PRICE="price_filter"
TYPE_VOLUME="volume_filter"
TYPE_OPEN_INTEREST="open_interest_filter"

def main(screener_config_file,summary_quote):
    screener_config = read_json_file(screener_config_file)
    symbols = get_symbols(screener_config.get(SYMBOLS_DIR))
    questions = get_questions(screener_config.get(QUESTIONS_DIR))

    passing = dict()
    for symbol in sorted(symbols):
        (passed,score) = screen_symbol(screener_config,symbol,questions)
        if passed:
            passing[symbol] = score

    if len(passing) == 0:
        print(f"\nno valid symbols found")
    else:
        print("\nValid Symbols")
        print("-------------")
    for symbol in passing.keys():
        score = passing.get(symbol)
        
        if summary_quote:
            quote = stock_quote(screener_config.get(ETRADE_CONFIG), symbol)
            print(f"\t{symbol:5s} (score={score:-6.2f}%, price=${quote.get_price():7.2f})")
        else:
            print(f"\t{symbol:5s} (score={score:-6.2f})%")

def stock_quote(etrade_config,symbol):
    quote = GLOBAL_QUOTE_CACHE.get(symbol,None)
    if quote:
        debug(f"returning cached quote for {symbol}")
        return quote
    
    debug(f"getting quote for {symbol}")
    quote = get_quote(etrade_config, symbol)
    GLOBAL_QUOTE_CACHE[symbol] = quote
    return quote

def screen_symbol(screener_config,symbol,questions):

    if fresh_blocker_screen(screener_config,symbol,questions) is False:
        debug(f"{symbol} failed fresh blocker screen")
        return (False,0.0)

    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    answers = dict()
    answers[CACHE_SYMBOL] = symbol

    true_count = 0
    total_count = 0
    for section in sorted(questions.keys()):
        for question in questions[section].get(QUESTION_LIST):
            question_id = question.get(QUESTION_ID)

            value = None
            expiration_timestamp = 0

            answers[question_id] = dict()

            (value, expiration_timestamp) = ask_question(screener_config,answer_file,symbol,section,question)

            # Save the answers
            answers[question_id][CACHE_VALUE] = value
            answers[question_id][CACHE_EXPIRATION_TIMESTAMP] = expiration_timestamp
            answers[question_id][CACHE_QUESTION] = question.get(QUESTION_TEXT)

            if isinstance(value,bool):
                total_count += 1
                if value is False:
                    if question.get(QUESTION_BLOCKER,False):
                        debug(f"skipping {symbol}, blocker question {question_id} failed")
                        cache_answers(answer_file,answers)
                        return (False,0.0)
                else:
                    true_count += 1
    
    cache_answers(answer_file,answers)
    return (True,float(true_count/total_count)*100)

def fresh_blocker_screen(screener_config,symbol,questions):
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    answers = get_all_answers_from_cache(answer_file)

    # Check for fresh blockers
    for section in sorted(questions.keys()):
        for question in questions[section].get(QUESTION_LIST):
            question_id = question.get(QUESTION_ID,"none")
            if not question_id in answers.keys():
                continue
            if question.get(QUESTION_BLOCKER,False) is False:
                continue
            if question_id in answers.keys():
                if get_current_timestamp() < answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,0):
                    value = answers[question_id].get(CACHE_VALUE)
                    if value is False:
                        debug(f"'{question.get(QUESTION_TEXT)}' is a blocker and is false, failing screen")
                        return False

    return True

def cache_answers(answer_file,answers):
    debug(f"caching answers to {answer_file}")
    write_json_file(answer_file,answers)

def get_answer_file(cache_dir,symbol):
    return f"{cache_dir}/{symbol.upper()}.json"

def get_all_answers_from_cache(cache_file):
    answers = dict()
    try:
        answers = read_json_file(cache_file)
    except Exception as e:
        pass
    return answers

def check_price(screener_config,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    try: 
        quote = stock_quote(screener_config.get(ETRADE_CONFIG), symbol)
    except SymbolNotFoundError as e:
        debug(f"{symbol} does not exist")
        return (False,datetime.datetime(2037,12,31).timestamp())
    
    price = quote.get_price()

    price_min = question.get(PRICE_MIN,DEFAULT_PRICE_MIN)
    price_max = question.get(PRICE_MAX,DEFAULT_PRICE_MAX)

    # Price is greater than or euqal to price_mmin
    if price >= price_min:
        debug(f"{symbol} price ${price:.2f} is higher than {PRICE_MIN}(${price_min:.2f})")
    else:
        debug(f"{symbol} price ${price:.2f} is too low")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

    # Price is less than or equal to price_max
    if price <= price_max:
        debug(f"{symbol} price ${price:.2f} is lower than {PRICE_MAX}(${price_max:.2f})")
    else:
        debug(f"{symbol} price ${price:.2f} is too high")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    debug(f"check price for {symbol} passed")
    return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def check_volume(screener_config,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    try: 
        quote = stock_quote(screener_config.get(ETRADE_CONFIG), symbol)
    except SymbolNotFoundError as e:
        debug(f"{symbol} does not exist")
        return (False,datetime.datetime(2037,12,31).timestamp())
    
    avg_vol = quote.get_average_volume()
    volume_min = question.get(VOLUME_MIN,DEFAULT_VOLUME_MIN)

    # Volume must be greater than the minimum
    if avg_vol < volume_min:
        debug(f"{symbol} volume {avg_vol} is lower than {VOLUME_MIN}({volume_min})")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    debug(f"{symbol} volume {avg_vol} is high enough {VOLUME_MIN}({volume_min})")
    return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def check_open_interest(screener_config,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    try: 
        next_monthly = get_next_monthly_expiration()
        next_date = f"{next_monthly.year}-{next_monthly.month:02d}-{next_monthly.day:02d}"
        debug(f"fetching options chain for {symbol} {next_date}")
        option_chain = get_option_chain(screener_config.get(ETRADE_CONFIG), symbol, next_monthly)
    except Exception as e:
        debug(f"error fetching options chain: {e}")
        return (False,0)
    
    open_interest_min = question.get(OPEN_INTEREST_MIN,DEFAULT_OPEN_INTEREST_MIN)

    for strike_price in option_chain.get_strike_prices():
        call = option_chain.get_call_option(strike_price)
        open_interest = call.get_open_interest()
        if open_interest >= open_interest_min:
            debug(f"found open interest {open_interest} for {symbol} strike {strike_price} on {next_date}")
            return(True,next_monthly.timestamp())

    # Didn't find sufficient open interest
    debug(f"did not find sufficient open interest for {symbol} on {next_date}")
    return(False,next_monthly.timestamp())

def debug(message):
    if GLOBAL_VERBOSE:
        print(message)

def get_answer_from_cache(answer_file,symbol,question):
    question_id = question.get(QUESTION_ID)
    text = question.get(QUESTION_TEXT)

    answers = get_all_answers_from_cache(answer_file)

    # Create the question if needed
    if question_id in answers.keys():
        value = answers[question_id].get(CACHE_VALUE,None)
        expiration_timestamp = answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,None)

        if get_current_timestamp() < answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,0):
            debug(f"got fresh answer '{value}' from cache for '{text}'")
            return (value,expiration_timestamp)

    # Didn't find a fresh answer
    return (None,0)

def ask_question_sector(answer_file,symbol,section,question):
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    text = question.get(QUESTION_TEXT)
    sector_file = question.get(SECTOR_FILE,DEFAULT_SECTOR_FILE)

    sector_list = list()
    try:
        sector_list = read_json_file(sector_file)
    except Exception as e:
        print(e)
    
    if len(sector_list) == 0:
        value = input(f"\t{symbol}[{section}] {text} ")
        sector_list.append(value)
        write_json_file(sector_file,sector_list)
        return(value,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

    print(f"\n\tSelect a sector ({symbol})\n")
    count = 0
    for sector in sector_list:
        count += 1
        print(f"\t{count:-2d}. {sector}")

    value = input(f"\n\t{symbol}[{section}] {text} (or 'new' for a new sector) ")
    if value == "new":
        value = input(f"\t{symbol}[{section}] {text} ")
        sector_list.append(value)
        write_json_file(sector_file,sorted(sector_list))
        return(value,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    
    sector_value = sector_list[int(value)-1]
    return(sector_value,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def ask_question(screener_config,answer_file,symbol,section,question):
    question_type = question.get(QUESTION_TYPE)

    if question_type == TYPE_BOOLEAN:
        return ask_question_boolean(answer_file,symbol,section,question)
    elif question_type == TYPE_PRICE:
        return check_price(screener_config,answer_file,symbol,section,question)
    elif question_type == TYPE_VOLUME:
        return check_volume(screener_config,answer_file,symbol,section,question)
    elif question_type == TYPE_EARNINGS:
        return ask_question_earnings(answer_file,symbol,section,question)
    elif question_type == TYPE_SECTOR:
        return ask_question_sector(answer_file,symbol,section,question)
    elif question_type == TYPE_OPEN_INTEREST:
        return check_open_interest(screener_config,answer_file,symbol,section,question)
    else:
        text = question.get(QUESTION_TEXT)
        print(f"\t{symbol}[{section}] Unkown questions type {question_type}({text})")
    
    return (None,0)

def get_current_timestamp():
    return int(datetime.datetime.now().timestamp())

def ask_question_boolean(answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value is not None:
        return (value,expiration_timestamp)

    text = question.get(QUESTION_TEXT)
    value = input(f"\t{symbol}[{section}] {text} [y/N] ")
    if value.lower().startswith("y"):
        return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    else:
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def ask_question_earnings(answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(answer_file,symbol,question)
    if value is not None:
        return (value,expiration_timestamp)

    text = question.get(QUESTION_TEXT)
    next_monthly = get_next_monthly_expiration()

    while True:
        value = input(f"\t{symbol}[{section}] {text} (YYYY-MM-DD): ")
        match = re.search(r'^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$',value)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))

            earnings_date = datetime.datetime(year,month,day,0,00,1)
            if earnings_date < next_monthly:
                debug(f"earnings date {earnings_date} is before next_monthly={next_monthly}")
                return (False,int(earnings_date.timestamp() + (86400*3)))
            else:
                debug(f"earnings date {earnings_date} is after next_monthly={next_monthly}")
                return (True,int(earnings_date.timestamp() + (86400*3)))
        else:
            print("\n*** format error, try again MMMM-YY-DD***")

def get_questions(questions_dir):
    questions = dict()
    for file in glob.glob(f"{questions_dir}/*.json"):
        try:
            question_data = read_json_file(file)
            qname = question_data.get(QUESTION_NAME)
            questions[qname] = question_data
        except Exception as e:
            print(f"Could not read {file}: {e}")
    return questions

def get_symbols(symbols_dir):
    symbols = set()
    for file in glob.glob(f"{symbols_dir}/*"):
        with open(file,"r") as f:
            for line in f.readlines():
                for token in line.rstrip().split():
                    symbols.add(token)
    return symbols

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_SCREENER_CONFIG_FILE)
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-q','--quote', dest='summary_quote', required=False,default=False,action='store_true',help="Include a quote in the summary")
    args = parser.parse_args()
    GLOBAL_VERBOSE = args.verbose
    GLOBAL_QUOTE_CACHE = dict()
    main(args.config_file,args.summary_quote)

