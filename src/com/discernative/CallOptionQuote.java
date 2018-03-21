package com.discernative;
import java.util.Calendar;
class CallOptionQuote extends OptionChainQuote {
    public CallOptionQuote ( String symbol, Calendar date, Double strike ) {
        this.symbol = symbol;
        this.date = date;
        this.strike = strike;
    }
    public String getType() {
        return "Call";
    }
}
