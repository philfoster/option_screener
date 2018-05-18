package com.discernative.etradetools;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Properties;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.etrade.etws.market.QuoteData;

public class FollowChain {

    private static final long SLEEP_TIME_SECONDS = 3;
    private static final long SLEEP_TIME_MILLIS = SLEEP_TIME_SECONDS * 1000;

    private static final String DEFAULT_AUTH_TOKEN = "auth_token.dat";
    private static final String DEFAULT_COMMISSION_PROPERTY = "5.45";
    private static final String DEFAULT_ASSIGNMENT_FEE_PROPERTY = "4.95";

    public static void main(String[] args) {
        Scanner inputScanner = new Scanner ( System.in );
        String propertiesFile = args[0];
        
        Properties props = EtradeTools.getProperties ( propertiesFile );
        
        String authTokenFile = props.getProperty ( "auth_token", DEFAULT_AUTH_TOKEN );
        Double commission = new Double ( props.getProperty ( "commission", DEFAULT_COMMISSION_PROPERTY ) );
        Double assignmentFee = new Double ( props.getProperty ( "assignment_fee", DEFAULT_ASSIGNMENT_FEE_PROPERTY ) );
        
        
        // ZION:2018:4:20:CALL:50.000000
        System.out.println( "Enter the option string (Example=ZION:2018:4:20:CALL:50.000000) : " );
        String optionString = inputScanner.next();
        
        inputScanner.close();
        

        String symbol = null;
        Integer year = 0;
        Integer month = 0;
        Integer day = 0;
        String type = null;
        Double strike = 0.0;
        
        Pattern regexPattern = Pattern.compile("^([^:]+):(\\d\\d\\d\\d):(\\d\\d?):(\\d\\d?):(CALL|PUT):(\\d+.\\d+)$");
        Matcher match = regexPattern.matcher(optionString);
        
        if ( match.find() ) {
            symbol = match.group(1);
            year = new Integer ( match.group(2) );
            month = new Integer ( match.group(3) );
            day = new Integer ( match.group ( 4 ) );
            type = match.group ( 5 );
            strike = new Double ( match.group ( 6 ) );
        } else {
            System.out.println( "Did not match the correct format" );
            System.exit( 0 );
        }
        
        AuthToken authToken = EtradeTools.getAuthToken ( authTokenFile );
        
        ArrayList<String> symbolBatch = new ArrayList<String>();
        
        symbolBatch.add ( symbol );
        symbolBatch.add ( optionString );
        try {
            while ( true ) {
                Double stockAskPrice = 0.0;
                Double optionBidPrice = 0.0;
                
                for ( QuoteData quoteData : EtradeTools.getQuote ( authToken, symbolBatch ) ) {
                    String symbolDesc = quoteData.getAll().getSymbolDesc();
                    System.out.println( "Symbol desc: " + symbolDesc );
                    Pattern symbolRegexPattern = Pattern.compile("\\$(\\d\\S*) (Call|Put)");
                    
                    Matcher symbolMatch = symbolRegexPattern.matcher(symbolDesc);
                    if ( symbolMatch.find() ) {
                        optionBidPrice = quoteData.getAll().getBid();
                    } else {
                        stockAskPrice = quoteData.getAll().getAsk();
                    }
                }
                
                System.out.println( "Option bid: " + optionBidPrice );
                System.out.println( "Stock ask: " + stockAskPrice );
                System.out.println( "Strike Price: " + strike);
                
                Double intrinsicValue = stockAskPrice - strike;
                Double timeValue = optionBidPrice - intrinsicValue;
                Double gain = timeValue - ( ( assignmentFee + commission ) / 100 );
                Double gainPrct = ( 100 * gain ) / stockAskPrice;
                Double costBasis = ( stockAskPrice - optionBidPrice ) + ( commission / 100 );
                Double safetyNet = ( 1 - ( costBasis / stockAskPrice ) ) * 100;
                
                System.out.println(String.format( "Gain: $%.2f(%.2f%%)", gain*100, gainPrct ));
                Thread.sleep( SLEEP_TIME_MILLIS );
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
            System.exit( 0 );
        }
            
    }

}
