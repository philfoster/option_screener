import glob
import json
import os
import pandas as pd
import sys
import time

from etrade_tools import *
from os.path import expanduser
from pandas_datareader import data as pdr
from stock_chart_tools.utils import get_historical_data, EMA, OBV, SSO, MACD
from stock_chart_tools.utils import COLUMN_CLOSE, COLUMN_VOLUME, COLUMN_HIGH, COLUMN_LOW, MACD_DIVERGENCE, MACD_LABEL, OBV_LABEL, SS_K, SS_D

# Screener config items
CACHE_DIR="cache_dir"
ETRADE_CONFIG="etrade_config"
QUESTIONS_DIR="questions_directory"
SYMBOLS_DIR="symbols_directory"
SECTOR_QUESTION_ID="sector_question_id"

# Defaults
DEFAULT_CACHE_DIR=".answers"
DEFAULT_PRICE_MIN=15.0
DEFAULT_PRICE_MAX=375.0
DEFAULT_VOLUME_MIN=400000
DEFAULT_BETA_MAX=2.0
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
BETA_MAX="beta_max"
SECTOR_FILE="sector_file"
OPEN_INTEREST_MIN="open_interest_min"

# Cache constants
CACHE_SYMBOL="symbol"
CACHE_VALUE="value"
CACHE_EXPIRATION_TIMESTAMP="expiration_timestamp"
CACHE_QUESTION="question"

# Two hours
CACHE_FRESHNESS_SECONDS=60*60 * 4

# Quetion types
TYPE_BOOLEAN="boolean"
TYPE_EARNINGS="earnings_date"
TYPE_SECTOR="sector_selection"
TYPE_PRICE="price_filter"
TYPE_VOLUME="volume_filter"
TYPE_OPEN_INTEREST="open_interest_filter"
TYPE_BETA="beta_filter"

# Columns
THREE_DAY_EMA="3dayEMA"
FIVE_DAY_EMA="5dayEMA"
NINE_DAY_EMA="9dayEMA"
TWENTY_DAY_EMA="20dayEMA"
HUNDRED_DAY_EMA="100dayEMA"
VOL_THREE_DAY="Vol3DayEMA"
VOL_TWENTY_DAY="Vol20DayEMA"

def get_sector_from_cache(screener_config,symbol):
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    if not os.path.exists(expanduser(answer_file)):
        return None

    sector_question_id = screener_config.get(SECTOR_QUESTION_ID,None)
    if sector_question_id is None:
        return None

    answers = get_all_answers_from_cache(answer_file)
    answer = answers.get(sector_question_id,None)
    if answer:
        return answer.get(CACHE_VALUE,None)
    return None

def cache_answers(answer_file,answers):
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

def get_answer_from_cache(answer_file,symbol,question):
    question_id = question.get(QUESTION_ID)
    text = question.get(QUESTION_TEXT)

    answers = get_all_answers_from_cache(answer_file)

    # Create the question if needed
    if question_id in answers.keys():
        value = answers[question_id].get(CACHE_VALUE,None)
        expiration_timestamp = answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,None)

        if get_current_timestamp() < answers[question_id].get(CACHE_EXPIRATION_TIMESTAMP,0):
            return (value,expiration_timestamp)

    # Didn't find a fresh answer
    return (None,0)

def read_json_file(json_file):
    """ Read in a json file and return a json data structure """
    json_data = None
    with open(expanduser(json_file), "r") as cf:
        json_data = json.loads("".join(cf.readlines()))
    return json_data

def write_json_file(filename,data):
    with open(expanduser(filename), "w") as f:
        f.write(json.dumps(data,indent=2))

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
    for file in glob.glob(f"{expanduser(symbols_dir)}/*"):
        with open(file,"r") as f:
            for line in f.readlines():
                for token in line.rstrip().split():
                    symbols.add(token)
    return symbols

def get_current_timestamp():
    return int(datetime.datetime.now().timestamp())

def get_score(screener_config,symbol):
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    if not os.path.exists(expanduser(answer_file)):
        print(f"no data found for {symbol}")

    answers = get_all_answers_from_cache(answer_file)

    total_count = 0
    true_count = 0
    for key in answers:
        answer = answers.get(key)
        if isinstance(answer,dict):
            value = answer.get(CACHE_VALUE)
            if isinstance(value,bool):
                total_count += 1
                if value:
                    true_count += 1
                
    return 100 * float(true_count / total_count)

def get_cache_filename(symbol,cache_dir):
    return os.path.join(expanduser(cache_dir),f"{symbol}.year.cache")

def get_cached_historical_data(symbol,cache_dir):
    filename = get_cache_filename(symbol,cache_dir)
    try:
        file_mtime = os.path.getmtime(filename)
        if (time.time() - file_mtime) < CACHE_FRESHNESS_SECONDS:
            data = pd.read_csv(filename,index_col=0)
            return data
        else:
            print(f"{filename} cache is not fresh enough")
    except Exception as e:
        pass

    return None

def cache_historical_data(symbol,cache_dir,price_data):
    filename = get_cache_filename(symbol,cache_dir)
    price_data.to_csv(filename)

def get_two_year_data(symbol,cache_dir):

    # Try to get the price data from cache
    price_data = get_cached_historical_data(symbol,cache_dir)
    if price_data is not None:
        return price_data

    # Nothing fresh in the cache
    price_data = get_historical_data(symbol, 1000)

    price_data[THREE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],3)
    price_data[FIVE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],5)
    price_data[NINE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],9)
    price_data[TWENTY_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],20)
    price_data[HUNDRED_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],100)

    price_data[VOL_THREE_DAY] = EMA(price_data[COLUMN_VOLUME],3)
    price_data[VOL_TWENTY_DAY] = EMA(price_data[COLUMN_VOLUME],20)

    cache_historical_data(symbol,cache_dir,price_data)

    return price_data

def get_cache_filename(symbol,cache_dir):
    return os.path.join(expanduser(cache_dir),f"{symbol}.year.cache")

def get_cached_historical_data(symbol,cache_dir):
    filename = get_cache_filename(symbol,cache_dir)
    try:
        print(f"trying to get the cached data")
        file_mtime = os.path.getmtime(filename)
        if (time.time() - file_mtime) < CACHE_FRESHNESS_SECONDS:
            data = pd.read_csv(filename,index_col=0)
            print(f"found cached data for {symbol}")
            return data
        else:
            print(f"{filename} cache is not fresh enough")
    except Exception as e:
        print(f"could not get cached data for {symbol}: {e}")
        pass

    return None

def cache_historical_data(symbol,cache_dir,price_data):
    filename = get_cache_filename(symbol,cache_dir)
    price_data.to_csv(filename)

def get_one_year_data(symbol,cache_dir):

    # Try to get the price data from cache
    price_data = get_cached_historical_data(symbol,cache_dir)
    if price_data is not None:
        return price_data

    # Nothing fresh in the cache
    price_data = get_historical_data(symbol)

    price_data[THREE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],3)
    price_data[FIVE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],5)
    price_data[NINE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],9)
    price_data[TWENTY_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],20)
    price_data[HUNDRED_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],100)

    price_data[VOL_THREE_DAY] = EMA(price_data[COLUMN_VOLUME],3)
    price_data[VOL_TWENTY_DAY] = EMA(price_data[COLUMN_VOLUME],20)

    cache_historical_data(symbol,cache_dir,price_data)

    return price_data
