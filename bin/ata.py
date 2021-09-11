#! /usr/bin/python3

import argparse
import datetime
import pandas as pd
import yfinance as yf
import sys

from pandas_datareader import data as pdr
from etrade_tools import *

DEFAULT_SCREENER_CONFIG_FILE="stock_screener.json"

# Questions (technicals)
QUID_PRICE_TRENDING_UP="9a21bbe0-3971-48e2-a84f-e09fa871a916"
QUID_PRICE_ABOVE_20DAYEMA="153c0da1-461c-442c-ae7e-c0428823f3e7"
QUID_20DAYEMA_TRENDING_UP="dd2bbe54-a68c-4cd0-ac3d-26038d622318"
QUID_20DAYEMA_ABOVE_100DAYEMA="58735e6c-74f8-4c6b-8d73-6f7b7e942d71"
QUID_100DAYEMA_TRENDING_UP="0ba7df53-0911-4af6-b18c-e31e17c264a5"

FRESHNESS_DAYS=2
ONE_DAY = 24 * 60 * 60

# Columns
THREE_DAY_EMA="3dayEMA"
FIVE_DAY_EMA="5dayEMA"
NINE_DAY_EMA="9dayEMA"
TWENTY_DAY_EMA="20dayEMA"
HUNDRED_DAY_EMA="100dayEMA"

# Globals
global GLOBAL_VERBOSE

def main(screener_config,questions):
    symbols = get_symbols(screener_config.get(SYMBOLS_DIR))
    for symbol in sorted(symbols):
        analyze_symbol(screener_config,questions,symbol)

def analyze_symbol(screener_config,questions,symbol):
    print(f"analyzing symbol {symbol}")
    answer_file = get_answer_file(screener_config.get(CACHE_DIR),symbol)
    answers = get_all_answers_from_cache(answer_file)

    price_data = get_one_year_data(symbol)

    (value,timestamp) = is_price_uptrending(symbol,price_data,answers)
    (value,timestamp) = is_price_above_20dayEMA(symbol,price_data,answers)
    (value,timestamp) = is_20dayEMA_uptrending(symbol,price_data,answers)
    (value,timestamp) = is_20dayEMA_above_100dayEMA(symbol,price_data,answers)
    (value,timestamp) = is_100dayEMA_uptrending(symbol,price_data,answers)

    cache_answers(answer_file,answers)

def get_one_year_data(symbol):
    now = datetime.datetime.now()
    end_date = f"{now.year}-{now.month:02d}-{now.day:02d}"
    start_date = f"{now.year -1}-{now.month:02d}-{now.day:02d}"
    price_data = pdr.get_data_yahoo(symbol,start=start_date,end=end_date)

    price_data[THREE_DAY_EMA] = price_data['Close'].ewm(span=3,adjust=False).mean()
    price_data[FIVE_DAY_EMA] = price_data['Close'].ewm(span=5,adjust=False).mean()
    price_data[NINE_DAY_EMA] = price_data['Close'].ewm(span=9,adjust=False).mean()
    price_data[TWENTY_DAY_EMA] = price_data['Close'].ewm(span=20,adjust=False).mean()
    price_data[HUNDRED_DAY_EMA] = price_data['Close'].ewm(span=100,adjust=False).mean()

    return price_data

def is_fresh(cached_answer):
    now = datetime.datetime.now()
    cached_ts = cached_answer.get(CACHE_EXPIRATION_TIMESTAMP,0)
    if cached_ts > now.timestamp():
        return True
    return False

def is_price_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_PRICE_TRENDING_UP,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer for price trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for price trending up")

    try: 
        three_day_ema = get_last_value(price_data,THREE_DAY_EMA)
        five_day_ema = get_last_value(price_data,FIVE_DAY_EMA)
        nine_day_ema = get_last_value(price_data,NINE_DAY_EMA)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if three_day_ema > five_day_ema and five_day_ema > nine_day_ema:
        value = True

    if not QUID_PRICE_TRENDING_UP in answers.keys():
        answers[QUID_PRICE_TRENDING_UP] = dict()
        answers[QUID_PRICE_TRENDING_UP][CACHE_QUESTION] = "(automated) Is the price trending up?"

    answers[QUID_PRICE_TRENDING_UP][CACHE_VALUE] = value
    answers[QUID_PRICE_TRENDING_UP][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) 3dayEMA {three_day_ema} > 5dayEMA {five_day_ema} > 9dayEMA {nine_day_ema}")
    return (value,expiration_time)

def is_price_above_20dayEMA(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_PRICE_ABOVE_20DAYEMA,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer for price above 20dayEMA")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for price above 20dayEMA")

    try: 
        price = get_last_value(price_data,'Close')
        twenty_day_ema = get_last_value(price_data,TWENTY_DAY_EMA)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if price > twenty_day_ema:
        value = True

    if not QUID_PRICE_ABOVE_20DAYEMA in answers.keys():
        answers[QUID_PRICE_ABOVE_20DAYEMA] = dict()
        answers[QUID_PRICE_ABOVE_20DAYEMA][CACHE_QUESTION] = "(automated) Is the price above the 20 day?"

    answers[QUID_PRICE_ABOVE_20DAYEMA][CACHE_VALUE] = value
    answers[QUID_PRICE_ABOVE_20DAYEMA][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) price {price} > 20dayEMA {twenty_day_ema}")
    return (value,expiration_time)

def is_20dayEMA_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_20DAYEMA_TRENDING_UP,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer for 20dayEMA trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for 20dayEMA trending up")

    try: 
        twenty_day_ema = get_last_value(price_data,TWENTY_DAY_EMA)
        prev_twenty_day_ema = price_data[TWENTY_DAY_EMA].iloc[-5]
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if twenty_day_ema > prev_twenty_day_ema:
        value = True

    if not QUID_20DAYEMA_TRENDING_UP in answers.keys():
        answers[QUID_20DAYEMA_TRENDING_UP] = dict()
        answers[QUID_20DAYEMA_TRENDING_UP][CACHE_QUESTION] = "(automated) Is the 20dayEMA trending up?"

    answers[QUID_20DAYEMA_TRENDING_UP][CACHE_VALUE] = value
    answers[QUID_20DAYEMA_TRENDING_UP][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) 20dayEMA {twenty_day_ema} > 20dayEMA(five days ago) {prev_twenty_day_ema}")
    return (value,expiration_time)

def is_20dayEMA_above_100dayEMA(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_20DAYEMA_ABOVE_100DAYEMA,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer for 20dayEMA above 100dayEMA")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for 20dayEMA above 100dayEMA")

    try: 
        twenty_day_ema = get_last_value(price_data,TWENTY_DAY_EMA)
        hundred_day_ema = get_last_value(price_data,HUNDRED_DAY_EMA)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if twenty_day_ema > hundred_day_ema:
        value = True

    if not QUID_20DAYEMA_ABOVE_100DAYEMA in answers.keys():
        answers[QUID_20DAYEMA_ABOVE_100DAYEMA] = dict()
        answers[QUID_20DAYEMA_ABOVE_100DAYEMA][CACHE_QUESTION] = "(automated) Is the 20dayEMA above the 100dayEMA?"

    answers[QUID_20DAYEMA_ABOVE_100DAYEMA][CACHE_VALUE] = value
    answers[QUID_20DAYEMA_ABOVE_100DAYEMA][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) 20dayEMA {twenty_day_ema} > 100dayEMA {hundred_day_ema}")
    return (value,expiration_time)

def is_100dayEMA_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_100DAYEMA_TRENDING_UP,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer for 100dayEMA trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for 100dayEMA trending up")

    try: 
        hundred_day_ema = get_last_value(price_data,HUNDRED_DAY_EMA)
        prev_hundred_day_ema = price_data[HUNDRED_DAY_EMA].iloc[-5]
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if hundred_day_ema > prev_hundred_day_ema:
        value = True

    if not QUID_100DAYEMA_TRENDING_UP in answers.keys():
        answers[QUID_100DAYEMA_TRENDING_UP] = dict()
        answers[QUID_100DAYEMA_TRENDING_UP][CACHE_QUESTION] = "(automated) Is the 100dayEMA trending up?"

    answers[QUID_100DAYEMA_TRENDING_UP][CACHE_VALUE] = value
    answers[QUID_100DAYEMA_TRENDING_UP][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) 100dayEMA {hundred_day_ema} > 100dayEMA(five days ago) {prev_hundred_day_ema}")
    return (value,expiration_time)

def get_last_value(price_data,column_name):
    return price_data[column_name].iloc[-1]

def debug(message):
    if GLOBAL_VERBOSE:
        print(message)

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="screener configuration file", default=DEFAULT_SCREENER_CONFIG_FILE)
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    parser.add_argument('-s','--symbol', dest='symbol', required=False,default=None,help="Analyze a symbol")
    args = parser.parse_args()

    GLOBAL_VERBOSE = args.verbose

    yf.pdr_override()

    screener_config = read_json_file(args.config_file)
    questions = get_questions(screener_config.get(QUESTIONS_DIR))

    if args.symbol:
        analyze_symbol(screener_config,questions,args.symbol)
    else:
        main(screener_config,questions)

