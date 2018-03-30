/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
import java.util.Properties;

import java.util.ArrayList;
import java.util.Calendar;
import java.io.FileReader;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.HashMap;

class ITMScreener {
    private static final String DEFAULT_MIN_GAIN_PRCT_PROPERTY = "0.5";
    private static final String DEFAULT_AUTH_TOKEN = "auth_token.dat";
    private static final String DEFAULT_MIN_YIELD_PROPERTY = "1.0";
    private static final String DEFAULT_MIN_DAYS_PROPERTY = "14";
    private static final String DEFAULT_MAX_DAYS_PROPERTY = "60";
    private static final String DEFAULT_COMMISSION_PROPERTY = "5.45";
    private static final String DEFAULT_MIN_PRICE_PROPERTY = "25.0";
    private static final String DEFAULT_MAX_PRICE_PROPERTY = "80.0";
    private static final String DEFAULT_MIN_BID_PROPERTY = "0.2";
    private static final String DEFAULT_MIN_SAFETY_NET_PROPERTY = "5.0";
    
    private static final long DAY_IN_SECONDS = 60 * 60 * 24;
    private static final long DAY_IN_MILLIS = DAY_IN_SECONDS * 1000;

    public static void main ( String[] args ) {
        System.out.println ( "In the Money Covered Call Option Screener" );
        String propertiesFile = args[0];

        Properties argProperties = EtradeTools.getProperties ( propertiesFile );

        String outputFile = argProperties.getProperty( "output_file" );
        
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

        Calendar startTime = Calendar.getInstance();
        ArrayList<String> csv = screener ( authToken, symbols, argProperties );
        Calendar endTime = Calendar.getInstance();
                
        for ( String line : csv ) {
            System.out.println ( line );
        }
        
        System.out.println( String.format( "(elapsed time %.2f seconds)", (float) ( endTime.getTimeInMillis() - startTime.getTimeInMillis() ) / 1000 ) );

        if ( outputFile != null ) {
            BufferedWriter w = null;
            try {
                w = new BufferedWriter ( new FileWriter ( outputFile ) );    
                
                for ( String line : csv ) {
                    w.write( line  );
                    w.newLine();
                }
                w.close();
            } catch ( IOException e ) {
                e.printStackTrace();
                System.exit( 1 );
            }
           
            
           
        }
    }

    public static ArrayList<String> screener ( AuthToken authToken, ArrayList<String> symbols, Properties props ) {
    	Double minYield = new Double ( props.getProperty ("min_yeild", DEFAULT_MIN_YIELD_PROPERTY ) );
    	Integer minDays = new Integer ( props.getProperty( "min_days", DEFAULT_MIN_DAYS_PROPERTY ) );
    	Integer maxDays = new Integer ( props.getProperty( "max_days", DEFAULT_MAX_DAYS_PROPERTY ) );
    	Double minGainPrct = new Double ( props.getProperty("min_prct_gain", DEFAULT_MIN_GAIN_PRCT_PROPERTY ));
    	Double commission = new Double ( props.getProperty( "commission", DEFAULT_COMMISSION_PROPERTY ) );
    	Double minPrice = new Double ( props.getProperty( "min_price", DEFAULT_MIN_PRICE_PROPERTY ) );
    	Double maxPrice = new Double ( props.getProperty( "max_price", DEFAULT_MAX_PRICE_PROPERTY ) );
    	Double minBid = new Double ( props.getProperty( "min_bid", DEFAULT_MIN_BID_PROPERTY ) );
    	Double minSafetyNet = new Double ( props.getProperty( "min_safety_net", DEFAULT_MIN_SAFETY_NET_PROPERTY ) );
    	
    	ArrayList<String> csv = new ArrayList<String>();
    	
        ArrayList<StockQuote> quotes = EtradeTools.getStockQuotes ( authToken, symbols );
        ArrayList<OptionChainQuote> keepers = new ArrayList<OptionChainQuote>();
        HashMap<String, StockQuote> tickerMap = new HashMap<String, StockQuote>();

        Calendar now = Calendar.getInstance();
        long minDateMillis = now.getTimeInMillis() + ( minDays * DAY_IN_MILLIS );
        long maxDateMillis = now.getTimeInMillis() + ( maxDays * DAY_IN_MILLIS );
 
        DateFormat df = new SimpleDateFormat("yyyy-MM-dd");
        

        for ( StockQuote quote : quotes ) {
            String symbol = quote.getSymbol();
            
          
            if ( quote.getYield() < minYield ) {
                System.out.println( "skipping " + symbol + ", yield is too low" );
                continue;
            }
            
            if ( quote.getPrice() < minPrice ) { 
                System.out.println( "skipping " + symbol + ", price(" + quote.getPrice() + ") is too low" );
                continue;
            }
            
            if ( quote.getPrice() > maxPrice ) { 
                System.out.println( "skipping " + symbol + ", price(" + quote.getPrice() + ") is too high" );
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
                    System.out.println("skipping date for " + symbol +", " + df.format ( date.getTime() ) + " because it's too soon (min=" + df.format( minDateMillis )+ ")" );
                    
                    if ( authToken.getEnv() == EtradeTools.LIVE ) {
                        continue;
                    }
                }
                
                if ( date.getTimeInMillis() > maxDateMillis ) {
                    System.out.println("skipping date for " + symbol + ", " + df.format ( date.getTime() ) + ", because it's too far away (max=" + df.format( maxDateMillis ) + ")" );
                    continue;
                }
                
                ArrayList<OptionChainQuote> optionChainQuotes = EtradeTools.getCallOptionChainQuote ( authToken, symbol, date );
                
                for ( OptionChainQuote optionQuote : optionChainQuotes ) {
                    Double intrinsicValue = quote.getPrice() - optionQuote.getStrikePrice();
                    Double timeValue = optionQuote.getBid() - intrinsicValue;
                    Double gain = timeValue - ( commission / 100 );
                    Double gainPrct = ( 100 * gain ) / quote.getPrice();
                    Double costBasis = ( quote.getPrice() - optionQuote.getBid() ) + ( commission / 100 );
                    Double safetyNet = ( 1 - ( costBasis / quote.getPrice() ) ) * 100;
                    
                    if ( optionQuote.getStrikePrice() > quote.getPrice() ) {
                        System.out.println( "skipping '" + optionQuote.toString() + "', it's out of the money" );
                        continue;
                    }
                   
                    if ( gainPrct < minGainPrct ) {
                        System.out.println( String.format( "skipping '%s', the gain (%f) is too low (min=%f)", optionQuote.toString(), gain, minGainPrct ) );
                        continue;
                    }
                    
                    if ( optionQuote.getBid() < minBid ) {
                        System.out.println( "skipping '" + optionQuote.toString() + "', the bid is too low: " + optionQuote.getBid() );
                        continue;
                    }
                    
                    if ( safetyNet < minSafetyNet ) {
                        System.out.println( String.format("skipping '%s', safety net (%.2f) is less min_safety_net (%.2f)", optionQuote.toString(), safetyNet, minSafetyNet ) );
                        continue;
                    }
                    
                    System.out.println ( "adding " + optionQuote.toString() );
                    keepers.add( optionQuote );
                }
                
                // Put the symbol into the map 
                tickerMap.put (symbol, quote );                
            }
        }
        
        csv.add ( "Symbol, yield, expireDate, strike, bid, ask, gain, safety, days, gain basis points/day" );
        
        for ( OptionChainQuote oq : keepers ) {
            String symbol = oq.getSymbol();
            StockQuote sq = tickerMap.get ( symbol );
            Double price = 0.0;
            
            if ( sq == null ) {
                if ( authToken.getEnv() == EtradeTools.LIVE ) {
                    System.out.println( String.format ( "Error: %s does not exist in the ticket map", symbol ) );
                    continue;
                } else {
                    price = oq.getStrikePrice() - 2.0;
                }
            } else {
                price = sq.getPrice();
            }
            
            Double intrinsicValue = price - oq.getStrikePrice();
            Double timeValue = oq.getBid() - intrinsicValue;
            Double gain = timeValue - ( commission / 100 );
            Double gainPrct = ( 100 * gain ) / price;
            Double costBasis = ( price - oq.getBid() ) + ( commission / 100 );
            Double safetyNet = ( 1 - ( costBasis / price ) ) * 100;
            long daysToExpire = (int) ( ( oq.getDate().getTimeInMillis() - now.getTimeInMillis() ) / DAY_IN_MILLIS ); 
            
            Double gainPointsPerDay = ( gainPrct / daysToExpire ) * 100;            
            
            if ( gainPrct < minGainPrct ) {
                System.out.println( "skipping " + oq.toString() + ", the gain is too low: " + gainPrct );
                continue;
            }
            
            // Symbol, yield, expireDate, strike, bid, ask, gain, safety, days, gainPoints/day
            
            csv.add (
                String.format ( "%s,%.2f,%s,%.2f,%.2f,%.2f,%.2f%%,%.2f%%,%d,%.2f",
                    oq.getSymbol(), 
                    sq.getYield(),
                    oq.getDateString(), 
                    oq.getStrikePrice(), 
                    oq.getBid(), 
                    oq.getAsk(), 
                    gainPrct, 
                    safetyNet, 
                    daysToExpire, 
                    gainPointsPerDay
                    ) 
                );                             
        }
        return csv;
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
