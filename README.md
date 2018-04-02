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
    gain$                           - Gain (in dollars) if the option is exercised 
    gain%                           - Gain (percentage) if the option is exercised (gain / cost)
    safety                          - amount the underlier most drop in order to lose money
    max profit safety               - amount the underlier can drop and you still make max profit
    days                            - number of days before option expiration
    gain basis points/day           - hundredths of a percent gained per day if executed
    gain% with div                  - Gain (in dollars) including dividend (if applicable)
    safety with div                 - safety amount including dividend
    gain basis points/day with div  - hundredths of a perceent gained per day including dividend
    max profit safety with div      - amount the underlier can drop and you still make max profit including dividend

# Sample CSV 
    Symbol, price, p/e ratio, exDivDate, hasDiv, div, yield, cost, expireDate, strike, bid, ask, gain$, gain%, safety, days, gain basis points/day, gain% with div, safety with div, gain basis points/day with div
    CSCO,42.85,99999.99,2018-04-04,yes,0.33,3.08,3955.45,2018-05-18,40.00,3.35,3.45,44.55,1.04%,7.69%,47,2.21,1.81%,8.46,3.85
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,4765.45,2018-04-20,48.00,7.90,8.00,34.55,0.62%,14.14%,19,3.28,0.62%,14.14,3.28
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,4945.45,2018-04-20,50.00,6.10,6.20,54.55,0.98%,10.89%,19,5.17,0.98%,10.89,5.17
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,5030.45,2018-04-20,51.00,5.25,5.35,69.55,1.25%,9.36%,19,6.60,1.25%,9.36,6.60
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,5110.45,2018-04-20,52.00,4.45,4.55,89.55,1.61%,7.92%,19,8.49,1.61%,7.92,8.49
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,4865.45,2018-05-18,50.00,6.90,7.30,134.55,2.42%,12.33%,47,5.16,2.42%,12.33,5.16
    AMAT,55.50,20.94,2018-05-23,no,0.20,1.44,5035.45,2018-05-18,52.50,5.20,5.40,214.55,3.87%,9.27%,47,8.23,3.87%,9.27,8.23
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2733.45,2018-04-20,27.50,2.60,2.64,16.55,0.55%,8.52%,19,2.92,0.55%,8.52,2.92
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2383.45,2018-05-18,24.00,6.10,6.25,16.55,0.55%,20.23%,47,1.18,0.55%,20.23,1.18
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2468.45,2018-05-18,25.00,5.25,5.45,31.55,1.06%,17.39%,47,2.25,1.06%,17.39,2.25
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2548.45,2018-05-18,26.00,4.45,4.55,51.55,1.73%,14.71%,47,3.67,1.73%,14.71,3.67
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2618.45,2018-05-18,27.00,3.75,3.85,81.55,2.73%,12.37%,47,5.81,2.73%,12.37,5.81
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2688.45,2018-05-18,28.00,3.05,3.15,111.55,3.73%,10.03%,47,7.94,3.73%,10.03,7.94
    M,29.88,13.22,2018-03-14,no,0.38,5.05,2744.45,2018-05-18,29.00,2.49,2.53,155.55,5.21%,8.15%,47,11.08,5.21%,8.15,11.08
