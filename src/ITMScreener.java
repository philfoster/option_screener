import java.util.List;
import java.util.Calendar;
import com.etrade.etws.market.ExpirationDate;

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
