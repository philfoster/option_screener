/*
 * This file is subject to the terms and conditions defined in
 * file 'LICENSE.txt', which is part of this source code package.
 */
package com.discernative.etradetools;
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
