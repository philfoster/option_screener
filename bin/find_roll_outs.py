#! /usr/bin/python3
################################################################################
# find_roll_outs.py - this script will find options to roll out to if you find 
#                     yourself ITM near expiration and want to keep the shares.
################################################################################

import argparse
from etrade_tools import *

DEFAULT_CONFIG_FILE="./etc/etrade.json"
DEFAULT_PREFERENCES_FILE="./etc/stock_screener.json"

# This is how close the stock price needs to be to the strike price to run this
PRICE_PROXIMITY = 3

# This is the number of days before expiration where if the exdate is 
# within this time, there is a good chance of an ITM call being assigned
EXDATE_THRESHOLD = 10

# How much to weight the credit amount before dividing by days remaining
CREDIT_FACTOR = 5

# Reduce the buy up factor by this factor based on the days remaining
BUY_UP_SCORE_FACTOR = 5

# If there is a risky ex-date, multiply by this factor, and divide by the square of the days
RISKY_EXDATE_FACTOR = 0.5

# How many days out to look for rollouts
MAX_ROLLOUT_DAYS = 65
MIN_ROLLOUT_DAYS = 1

# This is the highest strike price to consider
MAX_STRIKE_FACTOR = 1.05

def main(config_file, symbol, existing_expiration, strike, min_days, max_days, verbose):

    quote = get_quote(config_file, symbol)
    price = quote.get_price()
    exdate = quote.get_exdate()
    dividend = quote.get_dividend()

    intrinsic_value = price - strike
    if intrinsic_value < 0:
        intrinsic_value = 0

    if price <= float(strike * (100 - PRICE_PROXIMITY)/100):
        print(f"{symbol}: price ${price:.2f} is more than {PRICE_PROXIMITY}% below strike {strike}")
        return

    call_option = get_call_option(config_file, symbol, existing_expiration, strike)
    if call_option is None:
        print(f"ERROR: could not find strike price {strike} for expiration {existing_expiration}")
        return
    
    print(f"{symbol}: ${price:.2f}")
    print(f"{call_option.get_display_symbol()}")

    ask = call_option.get_ask()
    time_value = ask - intrinsic_value
    tv_prct = 100 * (time_value / strike)

    itm_prct = 100 * (intrinsic_value / strike)

    print(f"Ask: {ask} (time value remaining=${time_value:.2f} / {tv_prct:.1f}%)")
    print(f"Current intrinsic value: ${intrinsic_value:.2f} ({itm_prct:.1f}%)")
    print(f"-----")
    
    if ask == 0:
        print("ERROR: ask is 0.00, maybe the market will open soon?")
        return

    option_chain_list = get_matching_option_chains(config_file, symbol, existing_expiration, min_days, max_days)
    for option_chain in option_chain_list:
        #roll_out_days = option_chain.get_expiration() - existing_expiration
        roll_out_days = option_chain.get_expiration() - datetime.datetime.now()
        risky_exdate = False
        div_ex_date_from_expiration = option_chain.get_expiration() - exdate
        if 0 < div_ex_date_from_expiration.days < EXDATE_THRESHOLD:
            risky_exdate = True
            
        for strike_price in option_chain.get_strike_prices():
            if strike_price < strike or strike_price > (price * MAX_STRIKE_FACTOR):
                # We only want options we could roll to
                continue
            call = option_chain.get_call_option(strike_price)
            bid = call.get_bid()
            if bid < ask:
                # Skip this, it would end with a debit
                continue

            credit = bid - ask
            buy_up = strike_price - strike

            total_gain = credit + buy_up
            total_prct = 100 * (total_gain / strike)
            bpd = 100 * (total_prct / roll_out_days.days)

            buy_up_prct = 100 * (buy_up/strike)
            credit_prct = 100 * (credit/strike)

            #buy_up_score = (100 * BUY_UP_SCORE_FACTOR * buy_up_prct) / (roll_out_days.days ** 2)
            #credit_score = (100 * CREDIT_FACTOR * credit ) / (roll_out_days.days ** 2)

            (total_score) = get_scores(buy_up_prct, credit_prct, roll_out_days.days, risky_exdate)

            print(f"{call.get_display_symbol():28}:  credit=${credit:5.2f}({credit_prct:4.2f}%) buy_up=${buy_up:5.2f}({buy_up_prct:4.2f}%) total={total_prct:5.2f}% days={roll_out_days.days:2d} bpd={bpd:5.2f} exdate_risk={risky_exdate} score={total_score:5.2f}")

def get_scores(buy_up_prct, credit_prct, num_days, risky_exdate):
    # What makes a good score?
    #   The best score has a good credit, and a roll up, is soon not later than the next monthly expiration
    # Points:
        # buy up score: multiply by 100 (on the order of 0.5 to 4.0)
        # credit score: multiply by 100 (on the order of 0.5 to 4.0)
        # credit score > buy up score: if buy up == 0, add 1 else divide credit by buy up (0.5 to 2.0)
        # Risky ex-date: subtract 2
        # Date: (10 - (days / 7) )/ 5 (0.00 to 1.8)
        
    # What makes a bad score?
    #   Too much buy up, not enough credit
    #   Has a risky exdate

    # Add credit and buy up
    #print(f"credit prct = {credit_prct:.2f}")
    #print(f"buy_up = {buy_up_prct:.2f}")

    score = (credit_prct + buy_up_prct)

    # Add the credit preference
    credit_preference = 0
    if buy_up_prct > 0:

        if buy_up_prct > credit_prct:
            credit_preference = credit_prct
        else:
            credit_preference = (credit_prct) + (buy_up_prct)

#    print(f"credit prefernece = {credit_preference:.2f}")
    score += credit_preference
        
    duration_factor = (10 - ((num_days / 7)*3))
    score += duration_factor

    exdate_factor = 0
    if risky_exdate:
        exdate_factor = -2

    score += exdate_factor

    return score

def get_matching_option_chains(config_file, symbol, existing_expiration, min_days, max_days):
    option_chain_list = list()
    dates = get_expiration_dates(config_file, symbol)

    for (expiration_date, expiration_type) in dates:
        if expiration_date > existing_expiration:
            elapsed = expiration_date - existing_expiration
            days = elapsed.days
            if min_days < days < max_days:
                option_chain = get_option_chain(config_file, symbol, expiration_date)
                if option_chain:
                    option_chain_list.append(option_chain)

    return option_chain_list

def get_call_option(config_file, symbol, existing_expiration, strike):
    option_chain = get_option_chain(config_file, symbol, existing_expiration)
    return option_chain.get_call_option(strike)

def get_expiration_dates(config_file, symbol):
    date_list = list()
    dates_data = get_options_expiration_dates(config_file, symbol)
    for date in dates_data.get("OptionExpireDateResponse").get("ExpirationDate"):
        year = date.get("year")
        month = date.get("month")
        day = date.get("day")
        expiration = datetime.datetime(year=int(year),month=int(month), day=int(day))
        date_list.append((expiration,date.get("expiryType")))
    return date_list
    

if __name__ == "__main__":
    # Setup the argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config-file', dest='config_file', help="etrade configuration file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-s','--symbol', dest='symbol', required=True,help="Symbol of the call" )
    parser.add_argument('-e','--expiration', dest='expiration', required=True,help="Symbol to search" )
    parser.add_argument('-p','--strike-price', dest='strike', required=True,help="Strike price" )
    parser.add_argument('--min-days', dest='min_days', required=False, default=MIN_ROLLOUT_DAYS,help="Minimum number of days until expiration" )
    parser.add_argument('--max-days', dest='max_days', required=False, default=MAX_ROLLOUT_DAYS,help="Maximum number of days until expiration" )
    parser.add_argument('-v','--verbose', dest='verbose', required=False,default=False,action='store_true',help="Increase verbosity")
    args = parser.parse_args()

    if args.expiration is not None:
        (y,m,d) = args.expiration.split("-")
        expiration = datetime.datetime(year=int(y),month=int(m), day=int(d))

    main(args.config_file, args.symbol, expiration, float(args.strike), int(args.min_days), int(args.max_days), args.verbose)
