package com.discernative;
import java.util.Calendar;

abstract class OptionChainQuote {
    protected String symbol;
    protected Calendar date;
    protected Double strike;

    protected Integer openInterest = 0;
    protected Double  bid = 0.0;
    protected Double  ask = 0.0;
    protected Integer bidSize = 0;
    protected Integer askSize = 0;
    protected Double  lastTrade = 0.0;
    
    // Accessor methods
    public String   getSymbol () { return this.symbol; };
    public Calendar getDate () { return this.date; };
    public Double   getStrikePrice () { return this.strike; };

    // accessor methods
    public Integer getOpenInterest() { return this.openInterest; };
    public Double  getBid() { return this.bid; };
    public Double  getAsk() { return this.ask; };
    public Integer getBidSize() { return this.bidSize; };
    public Integer getAskSize() { return this.askSize; };
    public Double  getLastTrade() { return this.lastTrade; };

    public void setOpenInterest (Integer i) { this.openInterest = i; };
    public void setBid ( Double bid ) { this.bid = bid; };
    public void setAsk ( Double ask ) { this.ask = ask; };
    public void setBidSize ( Integer i ) { this.bidSize = i; };
    public void setAskSize ( Integer i ) { this.askSize = i; };
    public void setLastTrade ( Double price ) { this.lastTrade = price; };

    public String toString() {
        int month = date.get ( Calendar.MONTH );
        int year = date.get ( Calendar.YEAR );
        int day = date.get ( Calendar.DAY_OF_MONTH );
        return String.format( "%s, %d-%d-%d, %f %s (bid: %f, ask %f)", 
            this.symbol, 
            year, 
            month, 
            day, 
            this.strike, 
            getType(), 
            this.bid, 
            this.ask );
    }

    public String getType() {
        return "unknown";
    }
}
