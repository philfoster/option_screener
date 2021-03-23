/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;

import com.etrade.etws.sdk.common.ETWSException;
import java.io.IOException;
import java.io.FileOutputStream;
import java.io.ObjectOutputStream;
import java.util.Properties;

class GetAuthToken {
    public static void main ( String[] args ) {
        String propertiesFile = args[0];

        Properties argProperties = EtradeTools.getProperties ( propertiesFile );

        String key = argProperties.getProperty ( "oauth_consumer_key" );
        String secret = argProperties.getProperty ( "consumer_secret" );
        String environment = argProperties.getProperty ( "environment" );

        System.out.println ( "Key='" + key + "'" );
        System.out.println ( "Secret='" + secret + "'" );
        System.out.println ( "environment='" + environment + "'" );

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

