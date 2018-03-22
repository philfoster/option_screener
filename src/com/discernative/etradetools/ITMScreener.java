/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
import java.util.List;
import java.util.Calendar;

class ITMScreener {
    public static void main ( String[] args ) {
        System.out.println ( "In the Money Covered Call Option Screener" );
        String filename = "auth_token.dat";

        AuthToken authToken = EtradeTools.getAuthToken ( filename );

        String symbol = "GOOG";

        List<Calendar> expirationDates = EtradeTools.getOptionExpirationDates ( authToken, symbol );

        for ( Calendar date : expirationDates ) {
            List<OptionChainQuote> optionChainQuotes = EtradeTools.getOptionChainQuote ( authToken, symbol, date );

            for ( OptionChainQuote quote : optionChainQuotes ) {
                System.out.println ( quote.toString() );
            }
            System.out.println ( "that is enough for now" );
            System.exit ( 0 );
        }
    }

}
