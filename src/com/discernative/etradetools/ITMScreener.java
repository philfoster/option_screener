/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
import java.util.Properties;

import com.etrade.etws.market.OptionQuote;

import java.util.ArrayList;
import java.util.Calendar;
import java.io.FileReader;
import java.io.BufferedReader;
import java.util.HashMap;

class ITMScreener {
    private static final String DEFAULT_MIN_GAIN_PRCT_PROPERTY = "0.5";
    private static final String DEFAULT_AUTH_TOKEN = "auth_token.dat";
    private static final String DEFAULT_MIN_YIELD_PROPERTY = "1.0";
    private static final String DEFAULT_MIN_DAYS_PROPERTY = "14";
    private static final String DEFAULT_MAX_DAYS_PROPERTY = "60";
    private static final String DEFAULT_COMMISSION_PROPERTY = "5.45";
    
    private static final long DAY_IN_SECONDS = 60 * 60 * 24;
    private static final long DAY_IN_MILLIS = DAY_IN_SECONDS * 1000;

    public static void main ( String[] args ) {
        System.out.println ( "In the Money Covered Call Option Screener" );
        String propertiesFile = args[0];

        Properties argProperties = EtradeTools.getProperties ( propertiesFile );

        String authTokenFile = argProperties.getProperty ( "auth_token" );
        if ( authTokenFile == null ) {
            authTokenFile = DEFAULT_AUTH_TOKEN;
        }

        String symbolFile = argProperties.getProperty ( "symbol_file" );
        if ( symbolFile == null ) {
            System.out.println ( "Error: no symbol_file defined in " + argProperties );
        }

        AuthToken authToken = EtradeTools.getAuthToken ( authTokenFile );

        ArrayList<String> symbols = readSymbols ( symbolFile );

        screener ( authToken, symbols, argProperties );
    }

    public static void screener ( AuthToken authToken, ArrayList<String> symbols, Properties props ) {
    	Double minYield = new Double ( props.getProperty ("min_yeild", DEFAULT_MIN_YIELD_PROPERTY ) );
    	Integer minDays = new Integer ( props.getProperty( "min_days", DEFAULT_MIN_DAYS_PROPERTY ) );
    	Integer maxDays = new Integer ( props.getProperty( "max_days", DEFAULT_MAX_DAYS_PROPERTY ) );
    	Double minGainPrct = new Double ( props.getProperty("min_prct_gain", DEFAULT_MIN_GAIN_PRCT_PROPERTY ));
    	Double commission = new Double ( props.getProperty( "commission", DEFAULT_COMMISSION_PROPERTY ) );
        
        ArrayList<StockQuote> quotes = EtradeTools.getStockQuotes ( authToken, symbols );
        ArrayList<OptionChainQuote> keepers = new ArrayList<OptionChainQuote>();
        HashMap<String, StockQuote> tickerMap = new HashMap<String, StockQuote>();

        for ( StockQuote quote : quotes ) {
            String symbol = quote.getSymbol();
            Double price = quote.getPrice();
            
            Calendar now = Calendar.getInstance();
            long minDateMillis = now.getTimeInMillis() + ( minDays * DAY_IN_MILLIS );
            long maxDateMillis = now.getTimeInMillis() + ( maxDays * DAY_IN_MILLIS );
           
            if ( quote.getYield() < minYield ) {
                System.out.println( "skipping " + symbol + ", yield is too low" );
                continue;
            }
            
            System.out.println ( "\n\nfetching option chain data for " + symbol );               

            if ( tickerMap.containsKey( symbol ) ) {
                // Don't pull the dates and quotes again if the symbol is already in the map
                // This likely will only affect the sandbox instance
                continue;
            }
                      
            ArrayList<Calendar> expirationDates = EtradeTools.getOptionExpirationDates ( authToken, symbol );

            for ( Calendar date : expirationDates ) {
                if ( date.getTimeInMillis() < minDateMillis ) {
                    System.out.println("skipping date because it's too soon" );
                    
                    if ( authToken.getEnv() == EtradeTools.LIVE ) {
                        continue;
                    }
                }
                
                if ( date.getTimeInMillis() > maxDateMillis ) {
                    System.out.println("skipping date because it's too far away" );
                    continue;
                }
                
                ArrayList<OptionChainQuote> optionChainQuotes = EtradeTools.getOptionChainQuote ( authToken, symbol, date );
                
                for ( OptionChainQuote optionQuote : optionChainQuotes ) {
                    Double intrinsicValue = quote.getPrice() - optionQuote.getStrikePrice();
                    Double timeValue = optionQuote.getBid() - intrinsicValue;
                    Double gain = timeValue - ( commission / 100 );
                    Double gainPrct = ( 100 * gain ) / quote.getPrice();
                   
                    if ( gainPrct < minGainPrct ) {
                        System.out.println( String.format( "skipping %s, the gain (%f) is too low (min=%f)", optionQuote.toString(), gain, minGainPrct ) );
                        continue;
                    }
                    
                    keepers.add( optionQuote );
                }
                
                // Put the symbol into the map 
                tickerMap.put (symbol, quote );                
            }
        }
        
        for ( OptionChainQuote oq : keepers ) {
            String symbol = oq.getSymbol();
            
            StockQuote sq = tickerMap.get ( symbol );
            
            if ( sq == null ) {
                System.out.println( String.format ( "Error: %s does not exist in the ticket map", symbol ) );
                continue;
            }
            
            Double intrinsicValue = sq.getPrice() - oq.getStrikePrice();
            Double timeValue = oq.getBid() - intrinsicValue;
            Double gain = timeValue - ( commission / 100 );
            Double gainPrct = ( 100 * gain ) / sq.getPrice();
            
            if ( gainPrct < minGainPrct ) {
                System.out.println( "skipping " + oq.toString() + ", the gain is too low: " + gainPrct );
            }
            
            System.out.println( String.format( "Keeper: %s (gain=%f%%)", oq.toString(), gainPrct) );
        }
        
    }

    public static ArrayList<String> readSymbols ( String filename ) { 
        ArrayList<String> symbolList = new ArrayList<String>();

        try {
            BufferedReader fileReader = new BufferedReader ( new FileReader ( filename ) );

            String line;
            while ( ( line = fileReader.readLine() ) != null ) {
                symbolList.add ( line );
            }
            fileReader.close();
        } catch ( Exception e ) {
            e.printStackTrace();
            System.exit ( 1 );
        }

        return symbolList;
    }
}
