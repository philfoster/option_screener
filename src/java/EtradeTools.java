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

import java.io.IOException;
import java.util.Scanner;
import java.util.ArrayList;
import java.io.FileInputStream;
import java.io.ObjectInputStream;

import java.math.BigDecimal;
import java.lang.reflect.*;

class EtradeTools {

    public static int LIVE = 1;
    public static int SANDBOX = 0;

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

    public static ClientRequest getAccessRequest ( String filename ) {
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

    public static ClientRequest getAccessRequest ( String key, String secret, int env, Token accessToken ) {

        // Create an access request
        ClientRequest accessRequest = new ClientRequest();
        if ( env == LIVE ) {
            accessRequest.setEnv( Environment.LIVE );
        } else {
            accessRequest.setEnv( Environment.SANDBOX );
        }

        // Setup the access request with the access token bits 
        accessRequest.setConsumerKey( key );
        accessRequest.setConsumerSecret( secret );
        accessRequest.setToken(accessToken.getToken());
        accessRequest.setTokenSecret(accessToken.getSecret());

        System.out.println ( "key=" + key );
        System.out.println ( "secret=" + secret );
        System.out.println ( "access token=" + accessToken.getToken());
        System.out.println ( "access secret=" + accessToken.getSecret());

        // Return the access request
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

    public static void getQuote ( ClientRequest clientRequest ) {
        
        ArrayList<String> symbols = new ArrayList<String>();
        MarketClient marketClient = new MarketClient(clientRequest);
        symbols.add("MU");
        symbols.add("DIS"); 
        
        QuoteResponse quoteResponse = new QuoteResponse();

        try {
            quoteResponse = marketClient.getQuote(symbols, new Boolean(true), DetailFlag.ALL);
        } catch (IOException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        } catch (ETWSException ex) {
            System.out.println ( "caught exception: " + ex );
            ex.printStackTrace();
            System.exit(1);
        }

        for(QuoteData quoteData : quoteResponse.getQuoteData())
        {
            System.out.println ( "Symbol: " + quoteData.getProduct().getSymbol() + " $" + quoteData.getAll().getLastTrade() + " (bid: " + quoteData.getAll().getBid() + " / ask: " + quoteData.getAll().getAsk() + ")" );
        }
    }
    
    public static void getOptionChain ( ClientRequest clientRequest ) {
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
        for( OptionChainPair optionPair : optionResponse.getOptionPairs() )
        {
            if ( optionPair.getCallCount() > 0 ) {
                for ( CallOptionChain callChain : optionPair.getCall() ) {
                    String rootSymbol = callChain.getRootSymbol();
                    BigDecimal strike = callChain.getStrikePrice();
                    ExpirationDate date = callChain.getExpireDate();
                    
                    Integer day = date.getDay(); 
                    String month = date.getMonth(); 
                    Integer year = date.getYear(); 
                    String expiryType = date.getExpiryType(); 
                    String strDate = new String ( year + "-" + month + "-" + day );
                    System.out.println ( "Call: " + rootSymbol + " strike=" + strike + " expiryDate=" + strDate + "(" + expiryType + ")"  );
                }
            }

            if ( optionPair.getPutCount() > 0 ) {
                for ( PutOptionChain putChain : optionPair.getPut() ) {
                    System.out.println ( "Put: strike=" + putChain.getStrikePrice() ); 
                }
            }
        }
    }
    
    public static void getOptionExpirationDates ( ClientRequest accessRequest, String symbol ) {
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

        System.out.println ( optionExpireResponse );
        showMethods ( optionExpireResponse );
    }

    public static void showMethods ( Object obj ) {
        Method[] methods = obj.getClass().getMethods();
        for(Method method : methods){
            System.out.println("method = " + method.getName());
        }
    }
}
