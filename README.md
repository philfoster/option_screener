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

# Running
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
