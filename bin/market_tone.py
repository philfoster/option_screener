#! /usr/bin/python3

from screener_tools import *
from stock_chart_tools.utils import get_historical_data, COLUMN_CLOSE, SMA, COLUMN_HIGH, COLUMN_LOW

DEFAULT_SCREENER_CONFIG_FILE="./etc/stock_screener.json"
DEFAULT_LOOKBACK_DAYS = 7

SYMBOL_VIX = "^VIX"
SYMBOL_SPX = "^GSPC"

CACHE_DIR = "~/.stock_screener"
SYMBOL_FILE = "./etc/sp500.txt"

BULLISH_VIX = 20
BEARISH_VIX = 30

def main(screener_config_file, symbol_file, cache_dir):
    screener_config = read_json_file(screener_config_file)

    vix, vix_5day_ema, vix_9day_ema = get_vix(cache_dir)
    vix_tone = "neutral"
    vix_trend = "improving"

    if vix >= BEARISH_VIX:
        vix_tone = "bearish"
    elif vix <= BULLISH_VIX:
        vix_tone = "bullish"

    if vix_9day_ema < vix_5day_ema:
        vix_trend = "worsening"

    ( spx, spx_5day_ema, spx_9day_ema )= get_spx(cache_dir)
    spx_trend = "improving"

    if spx_9day_ema > spx_5day_ema:
        spx_trend = "worsening"

    lookback_days = DEFAULT_LOOKBACK_DAYS
    symbols = get_symbols_from_file(symbol_file)

    golden_crosses = set()
    death_crosses = set()

    # 20 Day, 200 Day SMA Today's value
    over_20day = set()
    over_200day = set()

    # 20 Day, 200 Day SMA Yesterday's value
    yover_20day = set()
    yover_200day = set()

    # New highs this week
    new_highs = set()
    new_lows = set()

    count = 0
    for symbol in sorted(symbols):
        try:
            stock_data = get_two_year_data(symbol,cache_dir)
            stock_data["20dayEMA"] = EMA(stock_data[COLUMN_CLOSE],20)
            stock_data["50daySMA"] = SMA(stock_data[COLUMN_CLOSE],50)
            stock_data["200daySMA"] = SMA(stock_data[COLUMN_CLOSE],200)

            (g, d) = golden_cross(symbol, lookback_days, stock_data)
            golden_crosses.update(g)
            death_crosses.update(d)

            (o20, o200, yo20, yo200) = compare20dayEMA(symbol, stock_data)
            over_20day.update(o20)
            yover_20day.update(yo20)

            over_200day.update(o200)
            yover_200day.update(yo200)

            (nh, nl) = new_highs_and_lows(symbol, stock_data)
            new_highs.update(nh)
            new_lows.update(nl)

            count += 1
        except Exception as e:
            print(f"error with {symbol}: {e}")
            pass

    change_in_over20 = len(over_20day) - len(yover_20day)
    change_in_over200 = len(over_200day) - len(yover_200day)

    over20_prct = 100 *( len(over_20day) / count )
    over200_prct = 100 *( len(over_200day) / count )

    print( "################")
    print(f"# Market Tone  #")
    print( "################")
    print(f"Golden Crosses (last 7 days): {len(golden_crosses):3d}")
    print(f"Death Crosses  (last 7 days): {len(death_crosses):3d}")
    print(f"New 52w highs  (last 7 days): {len(new_highs):3d}")
    print(f"New 52w lows   (last 7 days): {len(new_lows):3d}")
    print(f"Over 20 day EMA             : {len(over_20day)} ({over20_prct:.2f}%, weekly change of {change_in_over20})")
    print(f"Over 200 day SMA            : {len(over_200day)} ({over200_prct:.2f}%, weekly change of {change_in_over200})")
    print(f"{SYMBOL_SPX}                       : {spx:.2f} (trend={spx_trend})")
    print(f"{SYMBOL_VIX}                        : {vix:.2f} (tone={vix_tone}, trend={vix_trend})")

    with open ("./golden_crosses.txt", "w") as f:
        for symbol in golden_crosses:
            f.write(f"{symbol}\n")

    with open ("./death_crosses.txt", "w") as f:
        for symbol in death_crosses:
            f.write(f"{symbol}\n")

def get_spx(cache_dir):
    stock_data = get_two_year_data(SYMBOL_SPX,cache_dir)
    stock_data["5dayEMA"] = EMA(stock_data[COLUMN_CLOSE],5)
    stock_data["9dayEMA"] = EMA(stock_data[COLUMN_CLOSE],9)

    return stock_data[COLUMN_CLOSE].iloc[-1], stock_data["5dayEMA"].iloc[-1], stock_data["9dayEMA"].iloc[-1]

def get_vix(cache_dir):
    stock_data = get_two_year_data(SYMBOL_VIX,cache_dir)
    stock_data["5dayEMA"] = EMA(stock_data[COLUMN_CLOSE],5)
    stock_data["9dayEMA"] = EMA(stock_data[COLUMN_CLOSE],9)

    return stock_data[COLUMN_CLOSE].iloc[-1], stock_data["5dayEMA"].iloc[-1], stock_data["9dayEMA"].iloc[-1]

def new_highs_and_lows(symbol, stock_data):
    highs = set()
    lows = set()

    last_year_highs = stock_data[COLUMN_HIGH][-250:]
    last_week_highs = stock_data[COLUMN_HIGH][-5:]

    last_year_lows = stock_data[COLUMN_LOW][-250:]
    last_week_lows = stock_data[COLUMN_LOW][-5:]

    if last_week_highs.max() >= last_year_highs.max():
        print(f"****** New high for {symbol}")
        highs.add(symbol)

    if last_week_lows.min() <= last_year_lows.min():
        print(f"****** New low for {symbol}")
        lows.add(symbol)

    return (highs, lows)

def golden_cross(symbol, lookback_days, stock_data):
    golden = set()
    death = set()
    for index in range(-1 * lookback_days, -1):
        sma50 = stock_data["50daySMA"].iloc[index]
        sma200 = stock_data["200daySMA"].iloc[index]
        date = stock_data.index[index]
        ysma50 = stock_data["50daySMA"].iloc[index -1]
        ysma200 = stock_data["200daySMA"].iloc[index -1]

#        print(f"{date} 50day={sma50:.2f} 200day={sma200:.2f}")
        if sma50 > sma200 and ysma50 <= ysma200:
            #print(f"\tgolden cross on {date.year}-{date.month:02d}-{date.day:02d}")
            print(f"\t{symbol}: golden cross on {date}")
            golden.add(symbol)

        if sma50 < sma200 and ysma50 >= ysma200:
            print(f"\t{symbol}: death cross on {date}")
            death.add(symbol)

    return (golden, death)
        
def compare20dayEMA(symbol, stock_data):
    o20 = set()
    o200 = set()

    yo20 = set()
    yo200 = set()

    price = stock_data[COLUMN_CLOSE].iloc[-1]

    if price > stock_data["20dayEMA"].iloc[-1]:
        o20.add(symbol)

    if price > stock_data["20dayEMA"].iloc[-6]:
        yo20.add(symbol)

    if price > stock_data["200daySMA"].iloc[-1]:
        o200.add(symbol)

    if price > stock_data["200daySMA"].iloc[-6]:
        yo200.add(symbol)

    return (o20, o200, yo20, yo200)
        

def get_symbols_from_file(file):
    symbols = set()
    with open(file,"r") as f:
        for line in f.readlines():
            for token in line.rstrip().split():
                symbols.add(token)
    return symbols
if __name__ == "__main__":
    main(DEFAULT_SCREENER_CONFIG_FILE, SYMBOL_FILE, CACHE_DIR)

