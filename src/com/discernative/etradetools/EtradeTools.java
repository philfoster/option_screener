package com.discernative.etradetools;
import com.etrade.etws.oauth.sdk.client.IOAuthClient;
import com.etrade.etws.oauth.sdk.client.OAuthClientImpl;
import com.etrade.etws.oauth.sdk.common.Token;
import com.etrade.etws.sdk.client.ClientRequest;
import com.etrade.etws.sdk.client.Environment;
import com.etrade.etws.sdk.common.ETWSException;

import com.etrade.etws.market.AllQuote;
import com.etrade.etws.market.DetailFlag;
import com.etrade.etws.market.QuoteData;
import com.etrade.etws.sdk.client.ClientRequest;
import com.etrade.etws.sdk.client.MarketClient;
import com.etrade.etws.market.QuoteResponse;

import com.etrade.etws.market.OptionChainPair;
import com.etrade.etws.market.OptionChainRequest;
import com.etrade.etws.market.OptionChainResponse;
import com.etrade.etws.market.PairType;
import com.etrade.etws.market.CallOptionChain;
import com.etrade.etws.market.PutOptionChain;
import com.etrade.etws.market.ExpirationDate;
import com.etrade.etws.market.OptionExpireDateGetRequest;
import com.etrade.etws.market.OptionExpireDateGetResponse;
import com.etrade.etws.market.OptionQuote;

import java.io.IOException;
import java.util.Scanner;
import java.util.ArrayList;
import java.util.List;
import java.util.Calendar;
import java.io.FileInputStream;
import java.io.ObjectInputStream;

import java.math.BigDecimal;
import java.lang.reflect.*;
import java.util.regex.*;

class EtradeTools {

    public static int LIVE = 1;
    public static int SANDBOX = 0;

    public static int MAX_BATCH_SIZE = 20;

    public static AuthToken getAuthToken ( String key, String secret, int env ) throws IOException, ETWSException {

        IOAuthClient authClient = OAuthClientImpl.getInstance();

        // Create the client request
        ClientRequest clientRequest = new ClientRequest();

        if ( env == LIVE ) {
            clientRequest.setEnv( Environment.LIVE );
        } else {
            clientRequest.setEnv( Environment.SANDBOX );
        }

        clientRequest.setConsumerKey( key );
        clientRequest.setConsumerSecret( secret );

        Token requestToken = authClient.getRequestToken ( clientRequest );

        clientRequest.setToken( requestToken.getToken() );
        clientRequest.setTokenSecret( requestToken.getSecret() );

        // Get the verifier code
        String authorizeURL = authClient.getAuthorizeUrl(clientRequest);
        String verificationCode = getVerificationCode ( authorizeURL );
        clientRequest.setVerifierCode(verificationCode);

        // get an access token
        Token accessToken = authClient.getAccessToken ( clientRequest );

        AuthToken a = new AuthToken ( key, secret, accessToken.getToken(), accessToken.getSecret(), env );
        return a;

    }

    public static AuthToken getAuthToken ( String filename ) {
        AuthToken authToken = null;
        try {
            FileInputStream fileIn = new FileInputStream( filename );
            ObjectInputStream in = new ObjectInputStream(fileIn);
            authToken = (AuthToken) in.readObject();
            in.close();
            fileIn.close();
        } catch (IOException i) {
            i.printStackTrace();
            System.exit(1);
        } catch (ClassNotFoundException c) {
            c.printStackTrace();
            System.exit(1);
        }

        return authToken;
    }

    public static ClientRequest getAccessRequest ( AuthToken authToken ) {
        // Create an access request
        ClientRequest accessRequest = new ClientRequest();
        if ( authToken.getEnv() == LIVE ) {
            accessRequest.setEnv( Environment.LIVE );
        } else {
            accessRequest.setEnv( Environment.SANDBOX );
        }

        // Setup the access request with the access token bits 
        accessRequest.setConsumerKey( authToken.getKey() );
        accessRequest.setConsumerSecret( authToken.getSecret() );
        accessRequest.setToken( authToken.getAccessToken() );
        accessRequest.setTokenSecret( authToken.getAccessSecret() );

        return accessRequest;
    }

    public static String getVerificationCode ( String url ) {
        Scanner inputScanner = new Scanner ( System.in );

        System.out.println ( "\n\n\nEnter the following URL into your browser, follow the prompts and copy the verification code\n\n" );
        System.out.println ( "URL = '" + url + "'" );

        System.out.print ( "\n\nEnter verification code: " );
        
        String verificationCode = inputScanner.next();
    
        return verificationCode;
    }

    public static List<QuoteData> getQuote ( AuthToken authToken, String symbol ) { 
        ArrayList<String> symbols = new ArrayList<String>();
        symbols.add(symbol);
        return getQuote ( authToken, symbols );
    }

    public static List<QuoteData> getQuote ( AuthToken authToken, ArrayList<String> symbols ) { 
        ClientRequest clientRequest = getAccessRequest ( authToken );
        MarketClient marketClient = new MarketClient(clientRequest);

        QuoteResponse quoteResponse = new QuoteResponse();
        ArrayList<QuoteData> allResponses = new ArrayList<QuoteData>();

        int count = 0;
        int total = 0;

        int batchSize = MAX_BATCH_SIZE;

        if ( authToken.getEnv() == SANDBOX ) {
            batchSize = 1;
        }

        System.out.println ( "Got " + count + " symbols" );

        ArrayList<String> batch = new ArrayList<String>();
        while ( count < symbols.size() ) {

            batch.add ( symbols.get ( count ) );
            count++;

            if ( count % batchSize == 0 || count == symbols.size() ) {
                try {
                    System.out.println ( "Fetching batch of size " + batch.size() );
                    total += batch.size();
                    quoteResponse = marketClient.getQuote( batch, new Boolean(true), DetailFlag.ALL);
                } catch (IOException ex) {
                    System.out.println ( "caught exception: " + ex );
                    ex.printStackTrace();
                    System.exit(1);
                } catch (ETWSException ex) {
                    System.out.println ( "caught exception: " + ex );
                    ex.printStackTrace();
                    System.exit(1);
                }

                // Now clear out the batch for the next run
                batch.clear();

                System.out.println ( "Number of quotes in the response: " + quoteResponse.getQuoteData().size() );
                for ( QuoteData q : quoteResponse.getQuoteData() ) {
                    System.out.println ( "Adding response for quote: " + q );
                    allResponses.add ( q );
                }
            }
        }

        if ( total == symbols.size() ) {
            System.out.println ( "\n\n\nPerfect! we matched the right number\n\n\n" );
        } else {
            System.out.println ( "\n\n\nShit! we wanted " + symbols.size() + " but only got " + total );
        }

        return allResponses;
    }
    

    public static void getOptionChain ( AuthToken authToken ) {
        ClientRequest clientRequest = getAccessRequest ( authToken );
        MarketClient marketClient = new MarketClient(clientRequest);
        OptionChainRequest req = new OptionChainRequest();
        req.setExpirationMonth("1"); // example values
        req.setExpirationYear("2018");
        req.setChainType("CALLPUT"); // example values
        req.setSkipAdjusted("FALSE");
        req.setUnderlier("GOOG");
        OptionChainResponse optionResponse = new OptionChainResponse();
        try {
            optionResponse = marketClient.getOptionChain(req);
        } catch (IOException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        } catch (ETWSException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        }

        // OptionExpireDateGetRequest req = new OptionExpireDateGetRequest();
        // req.setUnderlier("GOOG"); // underlier = GOOG for example
        // OptionExpireDateGetResponse response = client.getExpiryDates(req);

            // if ( optionPair.getPairType() == PairType.CALLONLY ) {
        for( OptionChainPair optionPair : optionResponse.getOptionPairs() ) {
            if ( optionPair.getCallCount() > 0 ) {
                for ( CallOptionChain callChain : optionPair.getCall() ) {
                    String rootSymbol = callChain.getRootSymbol();
                    BigDecimal strike = callChain.getStrikePrice();
                    ExpirationDate date = callChain.getExpireDate();
                    
                    Integer day = date.getDay(); 
                    String month = date.getMonth(); 
                    Integer year = date.getYear(); 

                }
            }

            if ( optionPair.getPutCount() > 0 ) {
                for ( PutOptionChain putChain : optionPair.getPut() ) {
                    System.out.println ( "Put: strike=" + putChain.getStrikePrice() ); 
                }
            }
        }
    }
    
    public static List<Calendar> getOptionExpirationDates ( AuthToken authToken, String symbol ) {
        ClientRequest accessRequest = getAccessRequest ( authToken );
        MarketClient marketClient = new MarketClient( accessRequest );

        OptionExpireDateGetRequest req = new OptionExpireDateGetRequest();
        req.setUnderlier( symbol );
        OptionExpireDateGetResponse optionExpireResponse = new OptionExpireDateGetResponse();
        try {
            optionExpireResponse = marketClient.getExpiryDates(req);
        } catch (IOException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        } catch (ETWSException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        }

        List<Calendar> dateList = new ArrayList<Calendar>();
        for ( ExpirationDate eDate : optionExpireResponse.getExpireDates() ) {
            Integer day = eDate.getDay();
            Integer year = eDate.getYear();
            Integer month = new Integer ( eDate.getMonth() );

            Calendar c = Calendar.getInstance();
            c.set ( year, month, day, 0, 0, 0 );
            dateList.add ( c );
            
        }
        return dateList;
    }

    public static void showMethods ( Object obj ) {
        Method[] methods = obj.getClass().getMethods();
        for(Method method : methods){
            System.out.println("method = " + method.getName());
        }
    }

    public static List<OptionChainQuote> getOptionChainQuote ( AuthToken authToken, String symbol, Calendar date ) {

        ClientRequest accessRequest = getAccessRequest ( authToken );
        MarketClient marketClient = new MarketClient( accessRequest );
        List<OptionChainQuote> chain = new ArrayList<OptionChainQuote>();

        // Get the option chain for a specific date and symbol
        // Foreach strike price
        //      get the call quote
        //          underlier:year:month:day:optiontype:strikePrice
        //      get the put qoute
        //      add to the list
        // return the list


        String month = new Integer( date.get ( Calendar.MONTH ) ).toString();
        String year = new Integer( date.get ( Calendar.YEAR ) ).toString();

        OptionChainRequest ocReq = new OptionChainRequest();

        if ( authToken.getEnv() == SANDBOX ) {
            // If on sandbox use current year
            year = "2018";
        }

        ocReq.setExpirationMonth( month );
        ocReq.setExpirationYear( year );
        ocReq.setChainType("CALLPUT"); // example values
        ocReq.setSkipAdjusted("FALSE");
        ocReq.setUnderlier( symbol );

        System.out.println ( String.format( "Fetching option chain for %s (year=%s/month=%s)", symbol, year, month ) );

        OptionChainResponse optionChainResponse = new OptionChainResponse();
        try {
            optionChainResponse = marketClient.getOptionChain( ocReq );
        } catch (IOException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            return chain;
        } catch (ETWSException ex) {
            System.out.println ( "caught exception in getOptionChainQuote: " + ex );
            ex.printStackTrace();
            return chain;
        }

        ArrayList<String> symbolBatch = new ArrayList<String>();

        for( OptionChainPair optionPair : optionChainResponse.getOptionPairs() ) {
            if ( optionPair.getCallCount() > 0 ) {
                // Batch the call options
                for ( CallOptionChain callChain : optionPair.getCall() ) {
                    String rootSymbol = callChain.getRootSymbol();
                    BigDecimal strike = callChain.getStrikePrice();
                    ExpirationDate expDate = callChain.getExpireDate();
                    
                    Integer theDay = expDate.getDay(); 
                    Integer theMonth = new Integer ( expDate.getMonth() ); 
                    Integer theYear = expDate.getYear(); 
                    String expiryType = expDate.getExpiryType(); 

                    // Fetch the call option quote
                    //          underlier:year:month:day:optiontype:strikePrice
                    String chainSymbol = new String ( String.format ( "%s:%d:%d:%d:%s:%f", symbol, theYear, theMonth, theDay, "CALL", strike ) );

                    symbolBatch.add ( chainSymbol );
                }
            }

            if ( optionPair.getPutCount() > 0 ) {
                
                // Process the put options
                for ( PutOptionChain putChain : optionPair.getPut() ) {
                    String rootSymbol = putChain.getRootSymbol();
                    BigDecimal strike = putChain.getStrikePrice();
                    ExpirationDate expDate = putChain.getExpireDate();
                    
                    Integer theDay = expDate.getDay(); 
                    Integer theMonth = new Integer ( expDate.getMonth() ); 
                    Integer theYear = expDate.getYear(); 
                    String expiryType = expDate.getExpiryType(); 

                    // Fetch the put option quote
                    //          underlier:year:month:day:optiontype:strikePrice
                    String chainSymbol = new String ( String.format ( "%s:%d:%d:%d:%s:%f", symbol, theYear, theMonth, theDay, "PUT", strike ) );

                    symbolBatch.add ( chainSymbol );
                }
            }
        }

        Pattern regexPattern = Pattern.compile("\\$(\\d\\S*) (Call|Put)");

        for ( QuoteData quoteData : getQuote ( authToken, symbolBatch ) ) {

            String symbolDesc = quoteData.getAll().getSymbolDesc();
            String underlier = quoteData.getProduct().getSymbol();
            Double strike = new Double ( 0.0 );

            String type;

            // GOOG Apr 16 '11 $350 Put
            Matcher match = regexPattern.matcher(symbolDesc);
            if ( match.find() ) {
                strike = new Double ( match.group(1) );
                type = match.group(2);
            } else {
                continue;
            }

            OptionChainQuote quote;
            if ( type.equals ( "Call" ) ) {
                quote = new CallOptionQuote ( underlier + "(" + symbolDesc + ")", date, strike.doubleValue() );
            } else {
                quote = new PutOptionQuote ( underlier + "(" + symbolDesc + ")", date, strike.doubleValue() );
            }

            quote.setBid ( quoteData.getAll().getBid() );
            quote.setAsk ( quoteData.getAll().getAsk() );

            quote.setBidSize ( (int) quoteData.getAll().getBidSize() );
            quote.setAskSize ( (int) quoteData.getAll().getAskSize() );

            quote.setLastTrade ( quoteData.getAll().getLastTrade() );
            quote.setOpenInterest ( (int) quoteData.getAll().getOpenInterest() );

            chain.add ( quote );
        }

        return chain;
    }

}
