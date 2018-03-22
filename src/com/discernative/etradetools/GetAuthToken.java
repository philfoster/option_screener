/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;

import com.etrade.etws.sdk.common.ETWSException;
import java.io.IOException;
import java.io.FileOutputStream;
import java.io.ObjectOutputStream;

class GetAuthToken {
    public static void main ( String[] args ) {
        String key = args[0];
        String secret = args[1];
        String environment = args[2];

        String filename = "auth_token.dat";

        AuthToken authToken = null;

        int env = EtradeTools.SANDBOX;
        if ( environment.equals ( "live" ) ) {
            env = EtradeTools.LIVE;
        }

        try {
            authToken = EtradeTools.getAuthToken ( key, secret, env );
        } catch ( IOException e ) {
            System.out.println ( "Caught exception: " + e );
            System.exit ( 1 );
        } catch ( ETWSException e ) {
            System.out.println ( "Caught exception: " + e );
            System.exit ( 1 );
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

