# Java E*Trade API helper classes
    The idea here is to abstract away all of the E*Trade classes,
    which are a pain to work with and translate them into java
    friendly classes, like String, Double, Integer, Float.

# Requirements
    1. ant
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
        Example:
            # cat etrade.properties
            oauth_consumer_key=<put your info here>
            consumer_secret=<put your info here>
