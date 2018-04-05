/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
import java.util.Properties;
import java.text.SimpleDateFormat;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
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
    private static final String DEFAULT_MAX_PE_PROPERTY = "100.0";
    
    private static final String CSV_FORMAT_STRING = "itm_calls.%s.csv";
    
    static SimpleDateFormat dateFormatter = new SimpleDateFormat ( "yyyy-MM-dd" );


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
    
        ArrayList<String> symbols = EtradeTools.readSymbols ( symbolFile );
    
        Calendar startTime = Calendar.getInstance();
        ArrayList<String> csv = screener ( authToken, symbols, argProperties );
        Calendar endTime = Calendar.getInstance();
                
        for ( String line : csv ) {
            System.out.println ( line );
        }
        
        System.out.println( String.format( "(elapsed time %.2f seconds)", (float) ( endTime.getTimeInMillis() - startTime.getTimeInMillis() ) / 1000 ) );
    
        EtradeTools.writeFile ( CSV_FORMAT_STRING, csv );
    }

    public static ArrayList<String> screener ( AuthToken authToken, ArrayList<String> symbols, Properties props ) {
    	Double minYield = new Double ( props.getProperty ("min_yeild", DEFAULT_MIN_YIELD_PROPERTY ) );
    	Integer minDays = new Integer ( props.getProperty ( "min_days", DEFAULT_MIN_DAYS_PROPERTY ) );
    	Integer maxDays = new Integer ( props.getProperty ( "max_days", DEFAULT_MAX_DAYS_PROPERTY ) );
    	Double minGainPrct = new Double ( props.getProperty ("min_prct_gain", DEFAULT_MIN_GAIN_PRCT_PROPERTY ));
    	Double commission = new Double ( props.getProperty ( "commission", DEFAULT_COMMISSION_PROPERTY ) );
    	Double minPrice = new Double ( props.getProperty ( "min_price", DEFAULT_MIN_PRICE_PROPERTY ) );
    	Double maxPrice = new Double ( props.getProperty ( "max_price", DEFAULT_MAX_PRICE_PROPERTY ) );
    	Double minBid = new Double ( props.getProperty ( "min_bid", DEFAULT_MIN_BID_PROPERTY ) );
    	Double minSafetyNet = new Double ( props.getProperty ( "min_safety_net", DEFAULT_MIN_SAFETY_NET_PROPERTY ) );
    	Double maxPE = new Double ( props.getProperty ( "max_pe", DEFAULT_MAX_PE_PROPERTY ) );
    	
    	ArrayList<String> csv = new ArrayList<String>();
    	
        ArrayList<StockQuote> quotes = EtradeTools.getStockQuotes ( authToken, symbols );
        ArrayList<OptionChainQuote> keepers = new ArrayList<OptionChainQuote>();
        HashMap<String, StockQuote> tickerMap = new HashMap<String, StockQuote>();

        Date now = new Date();
 
        for ( StockQuote quote : quotes ) {
            String symbol = quote.getSymbol();
            
          
            if ( quote.getYield() < minYield ) {
                System.out.println( "skipping " + symbol + ", yield is too low" );
                continue;
            }
            
            if ( quote.getPE() > maxPE && maxPE != 0 ) {
                System.out.println( "skipping " + symbol + ", P/E Ratio is too high" );
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
                long deltaMillis = date.getTimeInMillis() - now.getTime();
                int deltaDays = (int) ( deltaMillis / EtradeTools.DAY_IN_MILLIS );
                
                
                if ( deltaDays < minDays ) {
                    System.out.println("skipping date for " + symbol +", " + EtradeTools.formatDate ( date ) + " because it's too soon (min=" + minDays + " days, delta=" + deltaDays + ")" );
                    
                    if ( authToken.getEnv() == EtradeTools.LIVE ) {
                        continue;
                    }
                }
                
                if ( deltaDays > maxDays ) {
                    System.out.println("skipping date for " + symbol + ", " + EtradeTools.formatDate ( date ) + ", because it's too far away (max=" + maxDays +" days, delta= " + deltaDays + ")" );
                    continue;
                }
                
                ArrayList<OptionChainQuote> optionChainQuotes = EtradeTools.getCallOptionChainQuote ( authToken, symbol, date, quote.getPrice(), EtradeTools.ITM );
                
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
        
        // Header
        String header = "Symbol, price, p/e ratio, exDivDate, hasDiv, div, yield, cost, expireDate, strike, bid, days, gain$, gain%, gain% with div, safety, max profit safety, gain basis points/day";
        csv.add ( header );
        
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
            Double dollarGain = gain * 100;
            
            Double gainPrct = ( 100 * gain ) / price;
            Double costBasis = ( price - oq.getBid() ) + ( commission / 100 );
            Double outOfPocket = costBasis * 100;
            Double safetyNet = ( 1 - ( costBasis / price ) ) * 100;
            long daysToExpire = (int) ( ( oq.getDate().getTimeInMillis() - now.getTime() ) / EtradeTools.DAY_IN_MILLIS ); 
            
            Double gainPointsPerDay = ( gainPrct / daysToExpire ) * 100;  
            String hasDiv = "no";
            Boolean includeDiv = Boolean.FALSE;
            
            // Add in the dividend stuff
            Double gainWithDiv = gain;
            Double costBasisWithDiv = costBasis;
            Double gainPrctWithDiv = gainPrct;
            Double safetyNetWithDiv = safetyNet;
            Double gainPointsPerDayWithDiv = gainPointsPerDay;
            Double maxProfitSafetyNet = ( 1 - ( oq.getStrikePrice() / price ) ) * 100;
            Double maxProfitSafetyNetWithDiv = maxProfitSafetyNet;
            
            
            if ( sq.getExDividendDate() != null ) {
                if ( sq.getExDividendDate().getTimeInMillis() > now.getTime() && sq.getExDividendDate().getTimeInMillis() < oq.getDate().getTimeInMillis() ) {
                    hasDiv = "yes";
                    includeDiv = Boolean.TRUE;
                }
            }
            
            if ( includeDiv ) {
                gainWithDiv += sq.getDividend();
                gainPrctWithDiv = ( 100 * gainWithDiv ) / price;
                costBasisWithDiv = ( price - oq.getBid() ) + ( commission / 100 ) - sq.getDividend();
                safetyNetWithDiv = ( 1 - ( costBasisWithDiv / price ) ) * 100;
                gainPointsPerDayWithDiv = ( gainPrctWithDiv / daysToExpire ) * 100;
                maxProfitSafetyNetWithDiv = ( 1 - ( ( oq.getStrikePrice() - sq.getDividend() ) / price ) ) * 100;
            }
                
            if ( gainPrct < minGainPrct ) {
                System.out.println( "skipping " + oq.toString() + ", the gain is too low: " + gainPrct );
                continue;
            }
            
            // Symbol, price, p/e ratio, 
            // exDivDate, hasDiv, div, 
            // yield, cost, expireDate, 
            // strike, bid, days
            // gain$, gain%, gain %with div
            // safety%, max profit safety%, gainPoint/Day
            
            csv.add (
                String.format ( "%s,%.2f,%.2f" + 
                        ",%s,%s,%.2f" + 
                        ",%.2f,%.2f,%s" + 
                        ",%.2f,%.2f,%d" + 
                        ",%.2f,%.2f%%,%.2f%%" + 
                        ",%.2f%%,%.2f%%,%.2f",
                    oq.getSymbol(), 
                    sq.getPrice(),
                    sq.getPE(),
                    
                    sq.getExDividendDateString(),
                    hasDiv,
                    sq.getDividend(),
                    
                    sq.getYield(),
                    outOfPocket,
                    oq.getDateString(), 
                    
                    oq.getStrikePrice(), 
                    oq.getBid(), 
                    daysToExpire, 
                    
                    dollarGain,
                    gainPrct, 
                    gainPrctWithDiv,
                    
                    safetyNetWithDiv,
                    maxProfitSafetyNetWithDiv,
                    gainPointsPerDayWithDiv
                    ) 
                );                             
        }
        return csv;
    }
}
