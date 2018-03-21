package com.discernative;
class AuthToken implements java.io.Serializable {
    private String key;
    private String secret;
    private String access_token;
    private String access_secret;
    private int env;

    public AuthToken ( String key, String secret, String access_token, String access_secret, int env ) {
        this.key = key;
        this.secret = secret;
        this.access_token = access_token;
        this.access_secret = access_secret;

        this.env = env;
    }

    public String getKey() {
        return this.key;
    }

    public String getSecret() {
        return this.secret;
    }

    public String getAccessToken() {
        return this.access_token;
    }

    public String getAccessSecret() {
        return this.access_secret;
    }

    public int getEnv() {
        return this.env;
    }

}


