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
QUID_VOLUME_HIGHER="9f407e44-e809-498f-942c-b688f19585d2"
QUID_OBV_POSITIVE="e30cc0ba-5b6e-43bf-a3d0-29a0b621a34d"
QUID_OBV_TRENDING_UP="87489c8b-4115-453d-8830-0324158d82d8"
QUID_MACD_TRENDING_UP="1a8c7983-b0d2-410f-82d4-1aa296f385b3"
QUID_MACD_DIVERGENCE_POSITIVE="f5f5352e-2af9-4734-bc34-4ef1f1aac763"
QUID_MACD_POSITIVE_VALUE="b67a5024-7b64-4712-b1a0-d1cf49c3ec33"

FRESHNESS_DAYS=1
ONE_DAY = 24 * 60 * 60
OBV_DAYS=-60

COLUMN_VOLUME="Volume"
COLUMN_CLOSE="Adj Close"

# Columns
THREE_DAY_EMA="3dayEMA"
FIVE_DAY_EMA="5dayEMA"
NINE_DAY_EMA="9dayEMA"
TWENTY_DAY_EMA="20dayEMA"
HUNDRED_DAY_EMA="100dayEMA"
VOL_THREE_DAY="Vol3DayEMA"
VOL_TWENTY_DAY="Vol20DayEMA"
ON_BALANCE_VOLUME="OnBalanceVolume"

# MACD Labels
MACD_LABEL="MACD"
MACD_DIVERGENCE="Divergence"
MACD_SIGNAL_LINE="SignalLine"

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
    (value,timestamp) = is_volume_heavy_lately(symbol,price_data,answers)
    (value,timestamp) = is_obv_positive(symbol,price_data,answers)
    (value,timestamp) = is_obv_uptrending(symbol,price_data,answers)
    (value,timestamp) = is_macd_uptrending(symbol,price_data,answers)
    (value,timestamp) = is_macd_divergence_positive(symbol,price_data,answers)
    (value,timestamp) = is_macd_positive(symbol,price_data,answers)

    cache_answers(answer_file,answers)

def get_one_year_data(symbol):
    now = datetime.datetime.now()
    end_date = f"{now.year}-{now.month:02d}-{now.day:02d}"
    start_date = f"{now.year -1}-{now.month:02d}-{now.day:02d}"
    price_data = pdr.get_data_yahoo(symbol,start=start_date,end=end_date)

    price_data[THREE_DAY_EMA] = price_data[COLUMN_CLOSE].ewm(span=3,adjust=False).mean()
    price_data[FIVE_DAY_EMA] = price_data[COLUMN_CLOSE].ewm(span=5,adjust=False).mean()
    price_data[NINE_DAY_EMA] = price_data[COLUMN_CLOSE].ewm(span=9,adjust=False).mean()
    price_data[TWENTY_DAY_EMA] = price_data[COLUMN_CLOSE].ewm(span=20,adjust=False).mean()
    price_data[HUNDRED_DAY_EMA] = price_data[COLUMN_CLOSE].ewm(span=100,adjust=False).mean()

    price_data[VOL_THREE_DAY] = price_data[COLUMN_VOLUME].ewm(span=3,adjust=False).mean()
    price_data[VOL_TWENTY_DAY] = price_data[COLUMN_VOLUME].ewm(span=20,adjust=False).mean()

    return price_data

def is_fresh(cached_answer):

    # Check to see if "-f" was passed, if so, ignore freshness
    if GLOBAL_FORCE:
        return False

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
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for price trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for price trending up")

    try: 
        three_day_ema = get_last_value(price_data,THREE_DAY_EMA)
        five_day_ema = get_last_value(price_data,FIVE_DAY_EMA)
        nine_day_ema = get_last_value(price_data,NINE_DAY_EMA)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if (three_day_ema > five_day_ema) and (five_day_ema > nine_day_ema):
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
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for price above 20dayEMA")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for price above 20dayEMA")

    try: 
        price = get_last_value(price_data,COLUMN_CLOSE)
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
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for 20dayEMA trending up")
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
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for 20dayEMA above 100dayEMA")
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
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for 100dayEMA trending up")
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

def is_volume_heavy_lately(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_VOLUME_HIGHER,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for heavy volume")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for heavy volume")

    try: 
        vol_3day = get_last_value(price_data,VOL_THREE_DAY)
        vol_20day = get_last_value(price_data,VOL_TWENTY_DAY)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if vol_3day > vol_20day:
        value = True

    if not QUID_VOLUME_HIGHER in answers.keys():
        answers[QUID_VOLUME_HIGHER] = dict()
        answers[QUID_VOLUME_HIGHER][CACHE_QUESTION] = "(automated) Is the volume greater than the average?"

    answers[QUID_VOLUME_HIGHER][CACHE_VALUE] = value
    answers[QUID_VOLUME_HIGHER][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) recent volume {int(vol_3day)} > normal volume {int(vol_20day)}")
    return (value,expiration_time)

def is_obv_positive(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_OBV_POSITIVE,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for obv positive")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for obv positive")

    try: 
        obv_data = on_balance_volume(price_data)
        current_obv = get_last_value(obv_data,ON_BALANCE_VOLUME)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if current_obv > 0:
        value = True

    if not QUID_OBV_POSITIVE in answers.keys():
        answers[QUID_OBV_POSITIVE] = dict()
        answers[QUID_OBV_POSITIVE][CACHE_QUESTION] = "(automated) Is the On Balance Volume positive?"

    answers[QUID_OBV_POSITIVE][CACHE_VALUE] = value
    answers[QUID_OBV_POSITIVE][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) on balance volume {current_obv} > 0")
    return (value,expiration_time)

def is_obv_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_OBV_TRENDING_UP,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for obv trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for obv trending up")

    try: 
        obv_data = on_balance_volume(price_data)
        obv_data[THREE_DAY_EMA] = obv_data[ON_BALANCE_VOLUME].ewm(span=3,adjust=False).mean()
        obv_data[NINE_DAY_EMA] = obv_data[ON_BALANCE_VOLUME].ewm(span=9,adjust=False).mean()

        three_day_ema = get_last_value(obv_data,THREE_DAY_EMA)
        nine_day_ema = get_last_value(obv_data,NINE_DAY_EMA)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if three_day_ema > nine_day_ema:
        value = True

    if not QUID_OBV_TRENDING_UP in answers.keys():
        answers[QUID_OBV_TRENDING_UP] = dict()
        answers[QUID_OBV_TRENDING_UP][CACHE_QUESTION] = "(automated) Is the On Balance Volume trending up?"

    answers[QUID_OBV_TRENDING_UP][CACHE_VALUE] = value
    answers[QUID_OBV_TRENDING_UP][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) OBV 3dayEMA {int(three_day_ema)} > OBV 9dayEMA {int(nine_day_ema)}")
    return (value,expiration_time)

def is_macd_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_MACD_TRENDING_UP,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for macd trending up")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for macd trending up")

    try: 
        macd_data = generate_macd(price_data)
        macd_data[THREE_DAY_EMA] = macd_data[MACD_LABEL].ewm(span=3,adjust=False).mean()
        macd_data[FIVE_DAY_EMA] = macd_data[MACD_LABEL].ewm(span=5,adjust=False).mean()

        macd_value = get_last_value(macd_data,MACD_LABEL)
        three_day_ema = get_last_value(macd_data,THREE_DAY_EMA)
        five_day_ema = get_last_value(macd_data,FIVE_DAY_EMA)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if (macd_value > three_day_ema) and (three_day_ema > five_day_ema):
        value = True

    if not QUID_MACD_TRENDING_UP in answers.keys():
        answers[QUID_MACD_TRENDING_UP] = dict()
        answers[QUID_MACD_TRENDING_UP][CACHE_QUESTION] = "(automated) Is the MACD trending up?"

    answers[QUID_MACD_TRENDING_UP][CACHE_VALUE] = value
    answers[QUID_MACD_TRENDING_UP][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) MACD value trending up {macd_value:.2f} > 3dayEMA {three_day_ema:.2f} > 5dayEMA {five_day_ema:.2f}")
    return (value,expiration_time)

def is_macd_divergence_positive(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_MACD_DIVERGENCE_POSITIVE,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for macd divergence positive")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for macd divergence positive")

    try: 
        macd_data = generate_macd(price_data)
        macd_histogram = get_last_value(macd_data,MACD_DIVERGENCE)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if macd_histogram > 0:
        value = True

    if not QUID_MACD_DIVERGENCE_POSITIVE in answers.keys():
        answers[QUID_MACD_DIVERGENCE_POSITIVE] = dict()
        answers[QUID_MACD_DIVERGENCE_POSITIVE][CACHE_QUESTION] = "(automated) Is the MACD Divergence Positive?"

    answers[QUID_MACD_DIVERGENCE_POSITIVE][CACHE_VALUE] = value
    answers[QUID_MACD_DIVERGENCE_POSITIVE][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) MACD Divergence {macd_histogram:.2f} > 0")
    return (value,expiration_time)

def is_macd_positive(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_MACD_POSITIVE_VALUE,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for macd value positive")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for macd value positive")

    try: 
        macd_data = generate_macd(price_data)
        macd_value = get_last_value(macd_data,MACD_LABEL)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if macd_value > 0:
        value = True

    if not QUID_MACD_POSITIVE_VALUE in answers.keys():
        answers[QUID_MACD_POSITIVE_VALUE] = dict()
        answers[QUID_MACD_POSITIVE_VALUE][CACHE_QUESTION] = "(automated) Is the MACD Value Positive?"

    answers[QUID_MACD_POSITIVE_VALUE][CACHE_VALUE] = value
    answers[QUID_MACD_POSITIVE_VALUE][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

    debug(f"{symbol} ({value}) MACD value {macd_value:.2f} > 0")
    return (value,expiration_time)

def on_balance_volume(stock_data):
    volume_data = pd.DataFrame(stock_data[COLUMN_VOLUME])[OBV_DAYS:]
    volume_data[COLUMN_CLOSE] = pd.DataFrame(stock_data[COLUMN_CLOSE])[OBV_DAYS:]

    for i, (index, row) in enumerate(volume_data.iterrows()):
        if i > 0:
            # Not the first row, so adjust OBV based on the price action
            prev_obv = volume_data.loc[volume_data.index[i - 1], ON_BALANCE_VOLUME]
            if row[COLUMN_CLOSE] > volume_data.loc[volume_data.index[i - 1], COLUMN_CLOSE]:
                # Up day
                obv = prev_obv + row[COLUMN_VOLUME]
            elif row[COLUMN_CLOSE] < volume_data.loc[volume_data.index[i - 1], COLUMN_CLOSE]:
                # Down day
                obv = prev_obv - row[COLUMN_VOLUME]
            else:
                # Equals, so keep the previous OBV value
                obv = prev_obv
        else:
            # First row, set prev_obv to zero
            obv = row[COLUMN_VOLUME]
            prev_obv = 0

        # Assign the obv value to the correct row
        volume_data.at[index, ON_BALANCE_VOLUME] = obv

    return volume_data

def generate_macd(stock_data,long=26,short=12,signal=9):
    macd = pd.DataFrame(stock_data[COLUMN_CLOSE])

    shortEMA = stock_data[COLUMN_CLOSE].ewm(span=short,adjust=False).mean()
    longEMA = stock_data[COLUMN_CLOSE].ewm(span=long,adjust=False).mean()

    macd[MACD_LABEL] = shortEMA - longEMA
    macd[MACD_SIGNAL_LINE] = macd[MACD_LABEL].ewm(span=signal,adjust=False).mean()
    macd[MACD_DIVERGENCE] = macd[MACD_LABEL] - macd[MACD_SIGNAL_LINE]

    return macd

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
    parser.add_argument('-f','--force', dest='force', required=False,default=False,action='store_true',help="Force update (ignore fresh answers)")
    args = parser.parse_args()

    GLOBAL_VERBOSE = args.verbose
    GLOBAL_FORCE = args.force

    yf.pdr_override()

    screener_config = read_json_file(args.config_file)
    questions = get_questions(screener_config.get(QUESTIONS_DIR))

    if args.symbol:
        analyze_symbol(screener_config,questions,args.symbol)
    else:
        main(screener_config,questions)

