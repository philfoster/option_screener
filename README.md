# Java E*Trade API helper classes
    The idea here is to abstract away all of the E*Trade classes,
    which are a pain to work with and translate them into java
    friendly classes, like String, Double, Integer, Float.

# Requirements
    1. ant and make
    2. third party jars put in ./lib
        commons-codec-1.3.jar
        commons-httpclient-3.1.jar
        commons-httpclient-contrib-ssl-3.1.jar
        commons-lang-2.4.jar
        commons-logging.jar
        log4j-1.2.15.jar
        xstream-1.3.1.jar
    3. E*Trade API jars put in ./lib
        etws-accounts-sdk-1.0.jar
        etws-common-connections-1.0.jar
        etws-market-sdk-1.0.jar
        etws-oauth-sdk-1.0.jar
        etws-order-sdk-1.0.jar
    4. Obtain your etrade API credentials and create a file called etrade.properties
        (change 'sandbox' to 'live' to switch to production environment)
        Example:
            # cat etrade.properties
            oauth_consumer_key=<put your info here>
            consumer_secret=<put your info here>
            environment=sandbox

# Running from the command line (with make)
    After configuring etrade.properties, you need to make an auth token
    Running 'make' will create an auth token if it does not already exist.

    You will be prompted with a URL. Paste that into a browser, follow the,
    prompts and then copy th everification code from the browser and paste
    it into the window. A new file 'auth_token.dat' will be created. This
    will last about two hours until it will need to be removed and 
    recreated.

    If you get an exception after things are working for a while, the auth
    token may have timed out, so 'make verclean' to delete the auth token.
    
    The next time you run 'make' it will create the auth token again.

# Running from eclipse
    You need to make two run targets with eclipse. The first should invoke 
    GetAuthToken, passing in etrade.properties as the only argument. The 
    second should call ITMScreener passing in screener.properties as the
    only argument.

    Run the auth token target to get an auth token (good for two hours,
    but it refreshes when you use it). The second will actually run the 
    screener tool.

# sceener.properties
    symbol_file=symbols.txt         # file containing a list of symbols
                                      one per line
    min_yield=0.1                   # minimum dividend yield for the underlier
    min_days=1                      # minimum days before option expiration
    max_days=70                     # maximum days before option expiration
    min_price=25                    # minimum price of the underlying stock
    max_price=70                    # maximum price of the underlying stock
    min_bid=0.2                     # minimum bid for the call option
    min_prct_gain=.5                # minimum gain obtained by selling the
                                      in-the-money covered call
    min_safety_net=7.5              # minimum amount that the underlier has 
                                      to fall before the strategy loses money
    max_pe=0.0                      # max p/e ratio for the underlying stock (0 to disable)
    commission                      # the cost to trade a buy/write at your brokerage
    auth_token=auth_token.dat       # the filename containing the serialized auth token

# CSV Column description
    Symbol                          - underlying stock ticker symbol
    price                           - the current price of the underlier
    p/e ratio                       - price to earnings ratio
    exDivDate                       - Ex-Dividend Date (if applicable)
    hasDiv                          - Whether the underlier will has a dividend during the time period
    div                             - amount of the dividend (typically quarterly amount)
    yield                           - current dividend yield (annual dividend / price)
    cost                            - out of pocket cost of the buy/write 
                                        ( (price * 100) + commission ) - option premium)
    expireDate                      - option expiration date
    strike                          - strike price of the call option
    bid                             - bid price of the call option
    ask                             - ask price of the call option
    days                            - number of days before option expiration
    gain$                           - Gain (in dollars) if the option is exercised 
    gain%                           - Gain (percentage) if the option is exercised (gain / cost)
    gain% with div                  - Gain (in dollars) including dividend (if applicable)
    safety with div                 - safety amount including dividend
    gain basis points/day with div  - hundredths of a perceent gained per day including dividend
    max profit safety with div      - amount the underlier can drop and you still make max profit including dividend

