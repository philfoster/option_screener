#! /usr/bin/python3

import argparse
import datetime
import pandas as pd
import yfinance as yf
import sys

from pandas_datareader import data as pdr
from etrade_tools import *
from stock_chart_tools.utils import get_historical_data, EMA, OBV, SSO, MACD
from stock_chart_tools.utils import COLUMN_CLOSE, COLUMN_VOLUME, COLUMN_HIGH, COLUMN_LOW, MACD_DIVERGENCE, MACD_LABEL, OBV_LABEL, SS_K, SS_D

DEFAULT_SCREENER_CONFIG_FILE="./etc/stock_screener.json"

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
QUID_SLOW_STOCHASTIC_POSITIVE="5f688dd9-8451-4f41-acc0-26c1e485fc5c"
QUID_SLOW_STOCHASTIC_UPTRENDING="8ebf903c-110a-4ff3-8c73-95ab6323fec8"
QUID_SLOW_STOCHASTIC_ABOVE_20="0122c7e7-bc9c-4879-8492-e8f9f7e25940"

FRESHNESS_DAYS=1
ONE_DAY = 24 * 60 * 60

# Columns
THREE_DAY_EMA="3dayEMA"
FIVE_DAY_EMA="5dayEMA"
NINE_DAY_EMA="9dayEMA"
TWENTY_DAY_EMA="20dayEMA"
HUNDRED_DAY_EMA="100dayEMA"
VOL_THREE_DAY="Vol3DayEMA"
VOL_TWENTY_DAY="Vol20DayEMA"

# Globals
global GLOBAL_VERBOSE

def main(screener_config,questions):
    symbols = get_symbols(screener_config.get(SYMBOLS_DIR))
    count = 0
    for symbol in sorted(symbols):
        analyze_symbol(screener_config,questions,symbol)
        count += 1
    if count == 0:
        print(f"no symbols found in {screener_config.get(SYMBOLS_DIR)}")

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
    (value,timestamp) = is_slow_stochastic_positive(symbol,price_data,answers)
    (value,timestamp) = is_slow_stochastic_uptrending(symbol,price_data,answers)
    (value,timestamp) = is_slow_stochastic_above_20(symbol,price_data,answers)

    cache_answers(answer_file,answers)

def get_one_year_data(symbol):
    price_data = get_historical_data(symbol)

    price_data[THREE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],3)
    price_data[FIVE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],5)
    price_data[NINE_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],9)
    price_data[TWENTY_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],20)
    price_data[HUNDRED_DAY_EMA] = EMA(price_data[COLUMN_CLOSE],100)

    price_data[VOL_THREE_DAY] = EMA(price_data[COLUMN_VOLUME],3)
    price_data[VOL_TWENTY_DAY] = EMA(price_data[COLUMN_VOLUME],20)

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

def store_result(answers,quid,value,expiration_time,question_text):
    if not quid in answers.keys():
        answers[quid] = dict()
        answers[quid][CACHE_QUESTION] = question_text

    answers[quid][CACHE_VALUE] = value
    answers[quid][CACHE_EXPIRATION_TIMESTAMP] = expiration_time

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

    store_result(answers,QUID_PRICE_TRENDING_UP,value,expiration_time, "(automated) Is the price trending up?")

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

    store_result(answers,QUID_PRICE_ABOVE_20DAYEMA,value,expiration_time,"(automated) Is the price above the 20 day?")

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

    store_result(answers,QUID_20DAYEMA_TRENDING_UP,value,expiration_time,"(automated) Is the 20dayEMA trending up?")

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

    store_result(answers,QUID_20DAYEMA_ABOVE_100DAYEMA,value,expiration_time,"(automated) Is the 20dayEMA above the 100dayEMA?")

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

    store_result(answers,QUID_100DAYEMA_TRENDING_UP,value,expiration_time,"(automated) Is the 100dayEMA trending up?")

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

    store_result(answers,QUID_VOLUME_HIGHER,value,expiration_time,"(automated) Is the volume greater than the average?")

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
        obv_data = OBV(price_data[COLUMN_CLOSE],price_data[COLUMN_VOLUME])
        current_obv = get_last_value(obv_data,OBV_LABEL)
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if current_obv > 0:
        value = True

    store_result(answers,QUID_OBV_POSITIVE,value,expiration_time,"(automated) Is the On Balance Volume positive?")

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
        obv_data = OBV(price_data[COLUMN_CLOSE],price_data[COLUMN_VOLUME])
        obv_data[THREE_DAY_EMA] = EMA(obv_data[OBV_LABEL],3)
        obv_data[NINE_DAY_EMA] = EMA(obv_data[OBV_LABEL],9)

        three_day_ema = get_last_value(obv_data,THREE_DAY_EMA)
        nine_day_ema = get_last_value(obv_data,NINE_DAY_EMA)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if three_day_ema > nine_day_ema:
        value = True

    store_result(answers,QUID_OBV_TRENDING_UP,value,expiration_time,"(automated) Is the On Balance Volume trending up?")

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
        macd_data = MACD(price_data[COLUMN_CLOSE])
        macd_data[THREE_DAY_EMA] = EMA(macd_data[MACD_LABEL],3)
        macd_data[FIVE_DAY_EMA] = EMA(macd_data[MACD_LABEL],5)

        macd_value = get_last_value(macd_data,MACD_LABEL)
        three_day_ema = get_last_value(macd_data,THREE_DAY_EMA)
        five_day_ema = get_last_value(macd_data,FIVE_DAY_EMA)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if (macd_value > three_day_ema) and (three_day_ema > five_day_ema):
        value = True

    store_result(answers,QUID_MACD_TRENDING_UP,value,expiration_time,"(automated) Is the MACD trending up?")

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
        macd_data = MACD(price_data[COLUMN_CLOSE])
        macd_divergence = get_last_value(macd_data,MACD_DIVERGENCE)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if macd_divergence > 0:
        value = True

    store_result(answers,QUID_MACD_DIVERGENCE_POSITIVE,value,expiration_time,"(automated) Is the MACD Divergence Positive?")

    debug(f"{symbol} ({value}) MACD Divergence {macd_divergence:.2f} > 0")
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
        macd_data = MACD(price_data[COLUMN_CLOSE])
        macd_value = get_last_value(macd_data,MACD_LABEL)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if macd_value > 0:
        value = True

    store_result(answers,QUID_MACD_POSITIVE_VALUE,value,expiration_time,"(automated) Is the MACD Value Positive?")

    debug(f"{symbol} ({value}) MACD value {macd_value:.2f} > 0")
    return (value,expiration_time)

def is_slow_stochastic_positive(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_SLOW_STOCHASTIC_POSITIVE,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for slow stochastic positive")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for slow stochastic positive")

    try: 
        ss = SSO(price_data[COLUMN_CLOSE],price_data[COLUMN_HIGH],price_data[COLUMN_LOW])
        k_val = get_last_value(ss,SS_K)
        d_val = get_last_value(ss,SS_D)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if k_val > d_val:
        value = True

    store_result(answers,QUID_SLOW_STOCHASTIC_POSITIVE,value,expiration_time,"(automated) Is the Slow Stochastic Positive?")

    debug(f"{symbol} ({value}) slow stochastic %K({k_val:.2f}) > %D({d_val:.2f})")
    return (value,expiration_time)

def is_slow_stochastic_uptrending(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_SLOW_STOCHASTIC_UPTRENDING,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for slow stochastic uptrending")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for slow stochastic uptrending")

    try: 
        ss = SSO(price_data[COLUMN_CLOSE],price_data[COLUMN_HIGH],price_data[COLUMN_LOW])

        # Get the 3day and 5day EMA of %K
        ss[THREE_DAY_EMA] = EMA(ss[SS_K],3)
        ss[FIVE_DAY_EMA] = EMA(ss[SS_K],5)

        three_day_ema = get_last_value(ss,THREE_DAY_EMA)
        five_day_ema = get_last_value(ss,FIVE_DAY_EMA)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if three_day_ema > five_day_ema:
        value = True

    store_result(answers,QUID_SLOW_STOCHASTIC_UPTRENDING,value,expiration_time,"(automated) Is the Slow Stochastic Uptrending?")

    debug(f"{symbol} ({value}) %K 3dayEMA({three_day_ema:.2f}) > 5dayEMA({five_day_ema:.2f})")

    return (value,expiration_time)

def is_slow_stochastic_above_20(symbol,price_data,answers):
    now = datetime.datetime.now()
    expiration_time = int(now.timestamp() + (ONE_DAY * FRESHNESS_DAYS))
    value = False

    cached_answer = answers.get(QUID_SLOW_STOCHASTIC_ABOVE_20,None)
    if cached_answer:
        if is_fresh(cached_answer):
            debug(f"{symbol} returning fresh answer {cached_answer.get(CACHE_VALUE)} for slow stochastic > 20")
            return (cached_answer.get(CACHE_VALUE),cached_answer.get(CACHE_EXPIRATION_TIMESTAMP))

    debug(f"{symbol} didn't find fresh answer for slow stochastic > 20")

    try: 
        ss = SSO(price_data[COLUMN_CLOSE],price_data[COLUMN_HIGH],price_data[COLUMN_LOW])
        k = get_last_value(ss,SS_K)
        
    except IndexError as e:
        print(f"{symbol} error: {e}")
        return (value,expiration_time)

    if k > 20:
        value = True

    store_result(answers,QUID_SLOW_STOCHASTIC_ABOVE_20,value,expiration_time,"(automated) Is the Slow Stochastic Above 20?")

    debug(f"{symbol} ({value}) slow stochastic %K ({k:.2f}) > 20")

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

