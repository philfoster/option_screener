#! /usr/bin/python3

import argparse
import datetime
import glob
import json
import re
from etrade_tools import *
from os.path import expanduser

DEFAULT_SCREENER_CONFIG_FILE="stock_screener.json"

# Screener config items
CACHE_DIR="cache_dir"
ETRADE_CONFIG="etrade_config"
QUESTIONS_DIR="questions_directory"
SYMBOLS_DIR="symbols_directory"
PRICE_MIN="price_min"
PRICE_MAX="price_max"
VOLUME_MIN="volume_min"

# Defaults
DEFAULT_CACHE_DIR=".answers"
DEFAULT_PRICE_MIN=15.0
DEFAULT_PRICE_MAX=375.0
DEFAULT_VOLUME_MIN=400000

# Question configuration
QUESTION_NAME="name"
QUESTION_LIST="questions"
QUESTION_TEXT="question"
QUESTION_TYPE="type"
QUESTION_ID="uuid"
QUESTION_BLOCKER="blocker"
QUESTION_EXPIRATION_DAYS="expiration_days"

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

def main(screener_config_file,verbose):
    screener_config = read_json_file(screener_config_file)
    symbols = get_symbols(screener_config.get(SYMBOLS_DIR))
    questions = get_questions(screener_config.get(QUESTIONS_DIR))

    passing = list()
    for symbol in sorted(symbols):
        passed = screen_symbol(screener_config,verbose,symbol,questions)
        if passed:
            passing.append(symbol)

    if len(passing) == 0:
        print(f"\nno valid symbols found")
    else:
        print("\nValid Symbols")
        print("-------------")
    for symbol in passing:
        print(f"\t{symbol}")

def screen_symbol(screener_config,verbose,symbol,questions):

    if fresh_blocker_screen(screener_config,verbose,symbol,questions) is False:
        debug(verbose,f"{symbol} failed fresh blocker screen")
        return False

    #if automatic_screen(screener_config,verbose,symbol) is False:
    #    debug(verbose,f"{symbol} failed automatic screen")
    #    return False

    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    answers = dict()
    answers[CACHE_SYMBOL] = symbol

    print(f"\nSymbol: {symbol}")

    non_blocker_false_count = 0
    for section in sorted(questions.keys()):
        for question in questions[section].get(QUESTION_LIST):
            question_id = question.get(QUESTION_ID)

            value = None
            expiration_timestamp = 0

            answers[question_id] = dict()

            (value, expiration_timestamp) = ask_question(verbose,screener_config,answer_file,symbol,section,question)

            # Save the answers
            answers[question_id][CACHE_VALUE] = value
            answers[question_id][CACHE_EXPIRATION_TIMESTAMP] = expiration_timestamp
            answers[question_id][CACHE_QUESTION] = question.get(QUESTION_TEXT)

            if isinstance(value,bool):
                if value is False:
                    if question.get(QUESTION_BLOCKER,False):
                        debug(verbose,f"skipping {symbol}, blocker question {question_id} failed")
                        cache_answers(verbose,answer_file,answers)
                        return False
                    else:
                        non_blocker_false_count = 0
    cache_answers(verbose,answer_file,answers)
    return True

def fresh_blocker_screen(screener_config,verbose,symbol,questions):
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    answers = get_all_answers_from_cache(verbose,answer_file)

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
                        debug(verbose,f"'{question.get(QUESTION_TEXT)}' is a blocker and is false, failing screen")
                        return False

    return True

def cache_answers(verbose,answer_file,answers):
    debug(verbose,f"caching answers to {answer_file}")
    write_json_file(expanduser(answer_file),answers)

def get_answer_file(cache_dir,symbol):
    return f"{cache_dir}/{symbol.upper()}.json"

def get_all_answers_from_cache(verbose,cache_file):
    answers = dict()
    try:
        answers = read_json_file(cache_file)
    except Exception as e:
        pass
    return answers

def check_price(screener_config,verbose,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(verbose,answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    try: 
        quote = get_quote(screener_config.get(ETRADE_CONFIG), symbol)
    except SymbolNotFoundError as e:
        debug(verbose,f"{symbol} does not exist")
        return (False,datetime.datetime(2037,12,31))
    
    price = quote.get_price()

    price_min = question.get(PRICE_MIN,DEFAULT_PRICE_MIN)
    price_max = question.get(PRICE_MAX,DEFAULT_PRICE_MAX)

    # Price is greater than or euqal to price_mmin
    if price >= price_min:
        debug(verbose,f"{symbol} price ${price:.2f} is higher than {PRICE_MIN}(${price_min:.2f})")
    else:
        debug(verbose,f"{symbol} price ${price:.2f} is too low")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

    # Price is less than or equal to price_max
    if price <= price_max:
        debug(verbose,f"{symbol} price ${price:.2f} is lower than {PRICE_MAX}(${price_max:.2f})")
    else:
        debug(verbose,f"{symbol} price ${price:.2f} is too high")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def check_volume(screener_config,verbose,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(verbose,answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    try: 
        quote = get_quote(screener_config.get(ETRADE_CONFIG), symbol)
    except SymbolNotFoundError as e:
        debug(verbose,f"{symbol} does not exist")
        return (False,datetime.datetime(2037,12,31))
    
    avg_vol = quote.get_average_volume()
    volume_min = question.get(VOLUME_MIN,DEFAULT_VOLUME_MIN)

    # Volume must be greater than the minimum
    if avg_vol < volume_min:
        debug(verbose,f"{symbol} volume {avg_vol} is lower than {VOLUME_MIN}({volume_min})")
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def automatic_screen(screener_config,verbose,symbol):
    try: 
        quote = get_quote(screener_config.get(ETRADE_CONFIG), symbol)
    except SymbolNotFoundError as e:
        debug(verbose,f"{symbol} does not exist")
        return False

    price = quote.get_price()
    avg_vol = quote.get_average_volume()

    price_min = screener_config.get(PRICE_MIN,DEFAULT_PRICE_MIN)
    price_max = screener_config.get(PRICE_MAX,DEFAULT_PRICE_MAX)
    vol_min = screener_config.get(AVG_VOL_MIN,DEFAULT_AVG_VOL_MIN)

    answers = get_all_answers_from_cache(verbose,get_answer_file(screener_config.get(CACHE_DIR),symbol))
    answers[CACHE_SYMBOL] = symbol

    # Price is greater than or euqal to price_mmin
    if price >= price_min:
        debug(verbose,f"{symbol} price ${price:.2f} is higher than {PRICE_MIN}(${price_min:.2f})")
    else:
        debug(verbose,f"{symbol} price ${price:.2f} is too low")
        return False

    # Price is less than or equal to price_max
    if price <= price_max:
        debug(verbose,f"{symbol} price ${price:.2f} is lower than {PRICE_MAX}(${price_max:.2f})")
    else:
        debug(verbose,f"{symbol} price ${price:.2f} is too high")
        return False

    # 10day volume is greater than volume_min
    if avg_vol >= vol_min:
        debug(verbose,f"{symbol} average volume {avg_vol} is higher than {AVG_VOL_MIN}(vol_min)")
    else:
        debug(verbose,f"{symbol} average volume {avg_vol} is too low")
        return False

    debug(verbose,f"{symbol} passed all automatic tests")
    return True

def debug(verbose,message):
    if verbose:
        print(message)

def get_answer_from_cache(verbose,answer_file,symbol,question):
    question_id = question.get(QUESTION_ID)
    text = question.get(QUESTION_TEXT)

    answers = get_all_answers_from_cache(verbose,answer_file)

    # Create the question if needed
    if question_id in answers.keys():
        value = answers[question_id].get(CACHE_VALUE,None)
        expiration_timestamp = answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,None)

        if get_current_timestamp() < answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,0):
            debug(verbose,f"got fresh answer '{value}' from cache for '{text}'")
            return (value,expiration_timestamp)

    # Didn't find a fresh answer
    return (None,0)

def ask_question(verbose,screener_config,answer_file,symbol,section,question):
    question_type = question.get(QUESTION_TYPE)

    if question_type == TYPE_BOOLEAN:
        return ask_question_boolean(verbose,answer_file,symbol,section,question)
    elif question_type == TYPE_PRICE:
        return check_price(screener_config,verbose,answer_file,symbol,section,question)
    elif question_type == TYPE_VOLUME:
        return check_volume(screener_config,verbose,answer_file,symbol,section,question)
    elif question_type == TYPE_EARNINGS:
        return ask_question_earnings(verbose,answer_file,symbol,section,question)
    else:
        text = question.get(QUESTION_TEXT)
        print(f"\t{symbol}[{section}] Unkown questions type {question_type}({text})")
    
    return (None,0)

def get_current_timestamp():
    return int(datetime.datetime.now().timestamp())

def ask_question_boolean(verbose,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(verbose,answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    text = question.get(QUESTION_TEXT)
    value  = input(f"\t{symbol}[{section}] {text} [y/N] ")
    if value.lower().startswith("y"):
        return(True,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))
    else:
        return(False,get_current_timestamp() + (86400 * question.get(QUESTION_EXPIRATION_DAYS,0)))

def ask_question_earnings(verbose,answer_file,symbol,section,question):
    # Get the boolean from cache and return it
    (value,expiration_timestamp) = get_answer_from_cache(verbose,answer_file,symbol,question)
    if value:
        return (value,expiration_timestamp)

    text = question.get(QUESTION_TEXT)
    next_monthly = get_next_monthly_expiration()

    while True:
        value  = input(f"\t{symbol}[{section}] {text} (YYYY-MM-DD): ")
        match = re.search(r'^\s*(\d\d\d\d)-(\d\d)-(\d\d)\s*$',value)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))

            earnings_date = datetime.datetime(year,month,day,0,00,1)
            if earnings_date < next_monthly:
                debug(verbose,f"earnings date {earnings_date} is before next_monthly={next_monthly}")
                return (False,int(earnings_date.timestamp()))
            else:
                debug(verbose,f"earnings date {earnings_date} is after next_monthly={next_monthly}")
                return (True,int(earnings_date.timestamp()))
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
    args = parser.parse_args()
    main(args.config_file,args.verbose)

