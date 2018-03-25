/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
import java.util.List;
import java.util.Calendar;
import java.util.Date;
import java.util.Properties;
import java.util.ArrayList;
import java.io.FileReader;
import java.io.BufferedReader;

class ITMScreener {
    public static String DEFAULT_AUTH_TOKEN = "auth_token.dat";

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
        ArrayList<StockQuote> quotes = EtradeTools.getStockQuotes ( authToken, symbols );

        for ( StockQuote quote : quotes ) {
            String symbol = quote.getSymbol();
            Double price = quote.getPrice();

            System.out.println ( String.format( "%s is trading at %.2f", symbol, price ) );
            System.out.println ( String.format( "\t%s: %s", "AnnualDividend", quote.getAnnualDividend() ) );
            System.out.println ( String.format( "\t%s: %s", "Dividend", quote.getDividend() ) );
            System.out.println ( String.format( "\t%s: %s", "EPS", quote.getEPS() ) );
            System.out.println ( String.format( "\t%s: %s", "ExDividendDate", quote.getExDividendDateString() ) );
            System.out.println ( String.format( "\t%s: %s", "High52", quote.getHigh52() ) );
            System.out.println ( String.format( "\t%s: %s", "Low52", quote.getLow52() ) );
            System.out.println ( String.format( "\t%s: %s", "PE", quote.getPE() ) );
            System.out.println ( String.format( "\t%s: %s", "Yield", quote.getYield() ) );

        /*
            System.out.println ( "fetching optin chain data for " + quote.getSymbol() );
            List<Calendar> expirationDates = EtradeTools.getOptionExpirationDates ( authToken, symbol );

            for ( Calendar date : expirationDates ) {
                List<OptionChainQuote> optionChainQuotes = EtradeTools.getOptionChainQuote ( authToken, symbol, date );

                for ( OptionChainQuote quote : optionChainQuotes ) {
                    System.out.println ( quote.toString() );
                }
                System.out.println ( "that is enough for now" );
                System.exit ( 0 );
            }
        */
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
