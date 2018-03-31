/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;

import java.util.Calendar;

class StockQuote {
    protected String symbol = "n/a";
    protected Double price = 0.0;

    protected Double   annualDividend = 0.0;
    protected Double   dividend = 0.0;
    protected Double   eps = 0.0;
    protected Calendar exDate = null;
    protected Double   forwardEps = 0.0;
    protected Double   high52 = 0.0;
    protected Double   low52 = 0.0;

    public StockQuote ( String symbol, Double price ) {
        this.symbol = symbol;
        this.price = price;
    }

    public String   getSymbol ()        { return this.symbol; }
    public Double   getPrice ()         { return this.price; }

    /*
     * Setters
     */
    public void setAnnualDividend  ( Double annualDividend ) { this.annualDividend = annualDividend; }
    public void setDividend        ( Double dividend ) { this.dividend = dividend; }
    public void setEPS             ( Double eps ) { this.eps = eps; }
    public void setExDividendDate  ( Calendar exDate ) { this.exDate = exDate; };
    public void setForwardEarnings ( Double forwardEps ) { this.forwardEps = forwardEps; }
    public void setHigh52          ( Double high52 ) { this.high52 = high52; }
    public void setLow52           ( Double low52 ) { this.low52 = low52; }

    /*
     * Getters
     */
    public Double   getAnnualDividend() { return this.annualDividend; }
    public Double   getDividend()       { return this.dividend; }
    public Double   getEPS()            { return this.eps; }
    public Calendar getExDividendDate() { return this.exDate; }
    public Double   getHigh52()         { return this.high52; }
    public Double   getLow52()          { return this.low52; }

    public Double getPE () { 
        /* 
         * Have to calculate the P/E Ratio
         */
        if ( this.eps == 0 ) {
            /*
             * but don't divide by zero
             */
            return new Double ( 0 );
        }
        
        Double pe = this.price / this.eps;
        if ( pe < 0 ) {
            return 99999.99;
        }
        
        return this.price / this.eps;
    }

    public Double getYield () {
        /* 
         * Have to calculate the yield
         */
        if ( price == 0 ) {
            /*
             * but don't divide by zero
             */
            return new Double ( 0 );
        }
        return ( this.annualDividend * 100 ) / this.price;
    }

    public String getExDividendDateString() {
        if ( this.exDate == null ) {
            return "n/a";
        }
        return String.format ( "%04d-%02d-%02d", this.exDate.get( Calendar.YEAR ), this.exDate.get ( Calendar.MONTH ) + 1, this.exDate.get( Calendar.DAY_OF_MONTH ) );

    }
}
