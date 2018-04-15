package com.discernative.etradetools;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import com.etrade.etws.market.QuoteData;

public class FollowChain {

    private static final long SLEEP_TIME_SECONDS = 3;
    private static final long SLEEP_TIME_MILLIS = SLEEP_TIME_SECONDS * 1000;
    private static final String authTokenFile = "auth_token.dat";

    public static void main(String[] args) {
        Scanner inputScanner = new Scanner ( System.in );
        
        // ZION:2018:4:20:CALL:50.000000
        System.out.println( "Enter the option string (Example=ZION:2018:4:20:CALL:50.000000) : " );
        String optionString = inputScanner.next();
        
        inputScanner.close();
        
        Pattern regexPattern = Pattern.compile("^([^:]+):(\\d\\d\\d\\d):(\\d\\d?):(\\d\\d?):(CALL|PUT):(\\d+.\\d+)$");
        Matcher match = regexPattern.matcher(optionString);
        
        String symbol = null;
        Integer year = 0;
        Integer month = 0;
        Integer day = 0;
        String type = null;
        Double strike = 0.0;
        
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
                Double stockPrice = 0.0;
                Double bidPrice = 0.0;
                
                for ( QuoteData quoteData : EtradeTools.getQuote ( authToken, symbolBatch ) ) {
                    System.out.println( "Hey, got a quote" );
                }
                
                Thread.sleep( SLEEP_TIME_MILLIS );
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
            System.exit( 0 );
        }
            
    }

}
