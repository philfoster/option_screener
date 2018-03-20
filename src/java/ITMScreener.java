import java.util.List;
import java.util.Calendar;
import com.etrade.etws.market.ExpirationDate;

class ITMScreener {
    public static void main ( String[] args ) {
        System.out.println ( "In the Money Covered Call Option Screener" );
        String key = "56ae833f8340c29ac16479271b7a8832";
        String secret = "4d7b35efabb5a65103cf8b2d586c2a8b";

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
