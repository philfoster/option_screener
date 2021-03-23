package com.discernative.etradetools;

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Properties;

public class CallScreener {

    private static final String DEFAULT_AUTH_TOKEN_PROPERTY = "auth_token.dat";
    private static final String DEFAULT_MIN_STOCK_PRICE_PROPERTY = "10.0";
    private static final String DEFAULT_MAX_ASK_PRICE_PROPERTY = "4.0";
    private static final String DEFAULT_STOCK_PRICE_FACTOR_PROPERTY = "50.0";
    private static final String DEFAULT_MIN_YIELD_PROPERTY = "1.0";
    private static final String DEFAULT_MAX_PE_PROPERTY = "30.0";
    private static final String DEFAULT_MIN_DAYS_PROPERTY = "14";
    private static final String DEFAULT_MAX_DAYS_PROPERTY = "60";
    private static final String DEFAULT_SAFETY_MARGIN_PROPERTY = "3.0";
    private static final String DEFAULT_PROJECTED_MOVE_PROPERTY = "1.0";
    private static final String DEFAULT_MIN_GAIN_PRCT_PROPERTY = "10.0";
    private static final String DEFAULT_DELTA_PROPERTY = "0.75";
    private static final String DEFAULT_COMMISSION_PROPERTY = "5.45";
    private static final String DEFAULT_MIN_GAIN_PROPERTY = "30.0";
    
    private static final String CSV_FORMAT_STRING = "call_options.%s.csv";

    public static void main(String[] args) {
        System.out.println ( "Call Option screener" );
        String propertiesFile = args[0];

        Properties argProperties = EtradeTools.getProperties ( propertiesFile );
                
        String authTokenFile = argProperties.getProperty ( "auth_token" );
        if ( authTokenFile == null ) {
            authTokenFile = DEFAULT_AUTH_TOKEN_PROPERTY;
        }
        
        String symbolFile = argProperties.getProperty ( "symbol_file" );
        if ( symbolFile == null ) {
            System.out.println ( "Error: no symbol_file defined in " + argProperties );
            System.exit(0);
        }
        
        AuthToken authToken = EtradeTools.getAuthToken ( authTokenFile );

        ArrayList<String> symbols = EtradeTools.readSymbols ( symbolFile );

        Calendar startTime = Calendar.getInstance();
        ArrayList<String> csv = callScreener ( authToken, symbols, argProperties );
        Calendar endTime = Calendar.getInstance();
                
        for ( String line : csv ) {
            System.out.println ( line );
        }
        
        System.out.println( String.format( "(elapsed time %.2f seconds)", (float) ( endTime.getTimeInMillis() - startTime.getTimeInMillis() ) / 1000 ) );
        EtradeTools.writeFile ( CSV_FORMAT_STRING, csv );
    }

    public static ArrayList<String> callScreener ( AuthToken authToken, ArrayList<String> symbols, Properties argProperties ) {
        ArrayList<String> output = new ArrayList<String>();
        HashMap<String, StockQuote> tickerMap = new HashMap<String, StockQuote>();
        ArrayList<OptionChainQuote> keepers = new ArrayList<OptionChainQuote>();
        Date now = new Date();
        
        Double commission = new Double ( argProperties.getProperty ( "commission",  DEFAULT_COMMISSION_PROPERTY ) );
        Double minStockPrice = new Double ( argProperties.getProperty ( "min_stock_price",  DEFAULT_MIN_STOCK_PRICE_PROPERTY ) );
        Double stockPriceFactor = new Double ( argProperties.getProperty ( "stock_price_factor", DEFAULT_STOCK_PRICE_FACTOR_PROPERTY ) );
        Double maxAskPrice = new Double ( argProperties.getProperty ( "max_ask", DEFAULT_MAX_ASK_PRICE_PROPERTY ) );
        
        Double minYield = new Double ( argProperties.getProperty ( "min_yield", DEFAULT_MIN_YIELD_PROPERTY ) );
        Double maxPE = new Double ( argProperties.getProperty ( "max_pe", DEFAULT_MAX_PE_PROPERTY ) );
        Integer minDays = new Integer ( argProperties.getProperty ( "min_days", DEFAULT_MIN_DAYS_PROPERTY ) );
        Integer maxDays = new Integer ( argProperties.getProperty ( "max_days", DEFAULT_MAX_DAYS_PROPERTY ) );
        
        Double minSafetyMargin = new Double ( argProperties.getProperty ( "safety_margin", DEFAULT_SAFETY_MARGIN_PROPERTY ) );
        Double minGain = new Double ( argProperties.getProperty ( "min_gain", DEFAULT_MIN_GAIN_PROPERTY ) );
        Double minGainPrct = new Double ( argProperties.getProperty ( "min_gain_prct", DEFAULT_MIN_GAIN_PRCT_PROPERTY ) );
        Double projectedMove = new Double ( argProperties.getProperty ( "projected_move", DEFAULT_PROJECTED_MOVE_PROPERTY ) );
        Double deltaFactor = new Double ( argProperties.getProperty ( "delta", DEFAULT_DELTA_PROPERTY ) );
        
        Double maxStockPrice = maxAskPrice * stockPriceFactor;
        
        ArrayList<StockQuote> quotes = EtradeTools.getStockQuotes ( authToken, symbols );
        for ( StockQuote quote : quotes ) {
         
            String symbol = quote.getSymbol();
            Double price = quote.getPrice();
            
            if ( price < minStockPrice ) {
                System.out.println( String.format( "skipping %s, price (%.2f) is too low (min_stock_price=%.2f)", symbol, price, minStockPrice ) );
                continue;
            }
            
            if ( price > maxStockPrice ) {
                System.out.println( String.format( "skipping %s, price (%.2f) is too high (max=%.2f)", symbol, price, maxStockPrice ) );
                continue;
            }
            
            if ( quote.getYield() < minYield ) {
                System.out.println( String.format( "skipping %s, yield (%.2f) is too low (min_yield=%.2f)", symbol, quote.getYield(), minYield ) );
                continue;
            }
            
            if ( quote.getPE() > maxPE ) {
                System.out.println( String.format( "skipping %s, P/E ratio (%.2f) is too high (max_pe=%.2f)", symbol, quote.getPE(), maxPE ) );
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
                    System.out.println("skipping date for " + symbol +", " + EtradeTools.formatDate ( date ) + " because it's too soon (min_days=" + minDays + " days, delta=" + deltaDays + ")" );
                    
                    if ( authToken.getEnv() == EtradeTools.LIVE ) {
                        continue;
                    }
                }
                
                if ( deltaDays > maxDays ) {
                    System.out.println("skipping date for " + symbol + ", " + EtradeTools.formatDate ( date ) + ", because it's too far away (max_days=" + maxDays +" days, delta= " + deltaDays + ")" );
                    continue;
                }
                
                ArrayList<OptionChainQuote> optionChainQuotes = EtradeTools.getCallOptionChainQuote ( authToken, symbol, date , quote.getPrice(), EtradeTools.ITM );
                
                for ( OptionChainQuote optionQuote : optionChainQuotes ) {
                    Double safetyMargin = getSafetyMargin ( price, optionQuote.getStrikePrice() );
                    
                    Double costBasis = optionQuote.getAsk() + ( commission / 100 );
                    Double priceTarget = getPriceTarget ( price, projectedMove );
                    
                    Double newOptionValue = getNewOptionValue ( price, priceTarget, optionQuote.getAsk(), deltaFactor );
                    
                    Double profit = ( newOptionValue - costBasis ) - ( commission / 100 );
                    Double profitDollars = profit * 100;
                    Double profitPrct = ( profit / costBasis ) * 100;
                    
                    if ( optionQuote.getStrikePrice() > quote.getPrice() ) {
                        System.out.println( "skipping '" + optionQuote.toString() + "', it's out of the money" );
                        continue;
                    }
                    
                    if ( optionQuote.getAsk() > maxAskPrice ) {
                        System.out.println( String.format( "skipping %s, ask(%.2f) is too high (max_ask_price=%.2f)", optionQuote.toString(), optionQuote.getAsk(), maxAskPrice  ) );
                        continue;
                    }
                    
                    if ( safetyMargin < minSafetyMargin ) {
                        System.out.println( String.format( "skipping %s, safety margin (%.2f) is too low (safety_margin=%.2f)", optionQuote.toString(), safetyMargin, minSafetyMargin ) );
                        continue;
                    }
       
                    /*
                    System.out.println( "price: " + price );
                    System.out.println( "new price: " + priceTarget );
                    System.out.println( "costBasis: " + costBasis );
                    System.out.println( "profit: " + profit );
                    System.out.println( "profitDollars: " + profitDollars );
                    System.out.println( "newOptionValue: " + newOptionValue );
                    System.out.println( "commission: " + commission );
                    */
                    
                    if ( profitPrct < minGainPrct ) {
                        System.out.println( String.format( "skipping %s, profit (%.2f%%) is too low (min_gain_prct=%.2f%%)", optionQuote.toString(), profitPrct, minGainPrct ) );
                        continue;
                    }
      
                    if ( profitDollars < minGain ) {
                        System.out.println( String.format( "skipping %s, profit ($%.2f) is too low (min_gain=$%.2f)", optionQuote.toString(), profitDollars, minGain ) );
                        continue;
                    }
                    // Apply filtering criteria here
                    keepers.add ( optionQuote );
                }
                tickerMap.put ( symbol, quote );
            }
        }
        
        output.add ( "symbol,price,p/e ratio,expire date,strike,bid,ask,safety margin,profit$ (on " + projectedMove + "% gain),profit% (on " + projectedMove + "% gain)" );
        for ( OptionChainQuote optionQuote : keepers ) {
            String symbol = optionQuote.getSymbol();
            StockQuote stockQuote = tickerMap.get ( symbol );
            Double price = 0.0;

            if ( stockQuote == null ) {
                if ( authToken.getEnv() == EtradeTools.LIVE ) {
                    System.out.println( String.format ( "Error: %s does not exist in the ticket map", symbol ) );
                    continue;
                } else {
                    price = optionQuote.getStrikePrice() - 2.0;
                }
            } else {
                price = stockQuote.getPrice();
            }

            Double safetyMargin = getSafetyMargin ( price, optionQuote.getStrikePrice() );

            Double costBasis = optionQuote.getAsk() + ( commission / 100 );
            Double priceTarget = getPriceTarget ( price, projectedMove );

            Double newOptionValue = getNewOptionValue ( price, priceTarget, optionQuote.getAsk(), deltaFactor );

            Double profit = ( newOptionValue - costBasis ) - ( commission / 100 );
            Double profitDollars = profit * 100;
            Double profitPrct = ( profit / costBasis ) * 100;


            // symbol, price, p/e ratio, 
            // expire date, strike, 
            // bid, ask, safety margin, 
            // gain$, gain prct
            output.add( String.format( 
                            "%s," +     // symbol
                            "$%.2f," +      // price
                            "%.2f," +        // p/e ratio
                            "%s," +         // expire date
                            "%.2f," +       // strike
                            "%.2f," +       // bid
                            "%.2f," +       // ask
                            "%.2f%%," +     // safety margin
                            "$%.2f," +      // gain$
                            "%.2f%%",        // gain%
                            symbol,
                            price,
                            stockQuote.getPE(),
                            optionQuote.getDateString(),
                            optionQuote.getStrikePrice(),
                            optionQuote.getBid(),
                            optionQuote.getAsk(),
                            safetyMargin,
                            profitDollars,
                            profitPrct
                    ) );

            
        }
        return output;
    }

    private static Double getNewOptionValue(Double stockPrice, Double priceTarget, Double optionPrice, Double deltaFactor) {
        Double priceChange = priceTarget - stockPrice;
        Double optionPriceChange = priceChange * deltaFactor;
        return optionPrice + optionPriceChange;
    }

    private static Double getPriceTarget(Double stockPrice, Double projectedMove) {
        return stockPrice * ( 1 + ( projectedMove / 100 ) );
    }

    private static Double getSafetyMargin(Double price, Double strike) {
        Double intrinsicValue = price - strike;
        return ( ( intrinsicValue * 100 ) / price );
    }
}
