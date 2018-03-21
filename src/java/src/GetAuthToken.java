import com.etrade.etws.account.Account;
import com.etrade.etws.account.AccountListResponse;
import com.etrade.etws.oauth.sdk.client.IOAuthClient;
import com.etrade.etws.oauth.sdk.client.OAuthClientImpl;
import com.etrade.etws.oauth.sdk.common.Token;
import com.etrade.etws.sdk.client.ClientRequest;
import com.etrade.etws.sdk.client.Environment;
import com.etrade.etws.sdk.common.ETWSException;
import java.io.IOException;
import java.io.FileOutputStream;
import java.io.ObjectOutputStream;

class GetAuthToken {
    public static void main ( String[] args ) {
        String key = args[0];
        String secret = args[1];
        String filename = "auth_token.dat";

        AuthToken authToken = null;

        int env = EtradeTools.SANDBOX;

        try {
            authToken = EtradeTools.getAuthToken ( key, secret, env );
        } catch ( IOException e ) {
            System.out.println ( "Caught exception: " + e );
            return;
        } catch ( ETWSException e ) {
            System.out.println ( "Caught exception: " + e );
            return;
        }

        serializeAuthToken ( filename, authToken );
    }

    public static void serializeAuthToken ( String filename, AuthToken authToken ) {
        try {
            FileOutputStream fileOut = new FileOutputStream( filename );
            ObjectOutputStream out = new ObjectOutputStream(fileOut);
            out.writeObject( authToken );
            out.close();
            fileOut.close();
            System.out.printf("Serialized data is saved in " + filename );
        } catch (IOException e) {
            System.out.println ( e );
        }
    }
}

